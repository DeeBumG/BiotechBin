import os
import datetime
import pymysql
import yfinance as yf
import getBioTickers
import scraper

# MySQL connection using environment variables
DB_HOST = os.environ.get('DATABASE_HOST')
DB_PORT = int(os.environ.get('DATABASE_PORT', 3306))
DB_USER = os.environ.get('DATABASE_USER')
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DB_NAME = os.environ.get('DATABASE_NAME')

connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def format_strike_price(strike):
    """Format strike price as 8-digit string (multiply by 1000)."""
    return f"{int(strike * 1000):08d}"

def build_option_symbol(ticker, exp_date, option_type, strike):
    """Construct the full option symbol."""
    date_part = exp_date.strftime('%y%m%d')
    type_letter = 'C' if option_type == 'call' else 'P'
    strike_part = format_strike_price(strike)
    return f"{ticker}{date_part}{type_letter}{strike_part}"

def fetch_and_store(tickers):
    today = datetime.date.today()
    data_to_insert = []

    with connection.cursor() as cursor:
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                expirations = stock.options
                if not expirations:
                    print(f"No options expirations for {ticker}")
                    continue

                next_exp = expirations[0]  # take the first expiration
                opt_chain = stock.option_chain(next_exp)

                # Top 2 CALLS by volume
                calls_sorted = opt_chain.calls.sort_values(by='volume', ascending=False)
                top_calls = calls_sorted.head(2)

                # Top 2 PUTS by volume
                puts_sorted = opt_chain.puts.sort_values(by='volume', ascending=False)
                top_puts = puts_sorted.head(2)

                all_options = [(row, 'call') for _, row in top_calls.iterrows()] + \
                              [(row, 'put') for _, row in top_puts.iterrows()]

                for option_row, option_type in all_options:
                    strike = option_row['strike']
                    symbol = build_option_symbol(ticker, datetime.datetime.strptime(next_exp, '%Y-%m-%d'), option_type, strike)

                    option_contract = yf.Ticker(symbol)
                    hist = option_contract.history(period="1d", interval="1m")
                    if hist.empty:
                        print(f"No price history for {symbol}")
                        continue

                    latest = hist.iloc[-1]
                    open_price = latest['Open']
                    high_price = latest['High']
                    low_price = latest['Low']
                    close_price = latest['Close']
                    volume = latest['Volume']

                    # Insert or collect data
                    # Ensure Ticker exists
                    cursor.execute("SELECT id FROM tickers WHERE symbol = %s", (ticker,))
                    ticker_row = cursor.fetchone()
                    if not ticker_row:
                        cursor.execute("INSERT INTO tickers (symbol) VALUES (%s)", (ticker,))
                        ticker_id = cursor.lastrowid
                    else:
                        ticker_id = ticker_row['id']

                    # Ensure Option exists
                    cursor.execute("""
                        SELECT id FROM options
                        WHERE ticker_id = %s AND expiration_date = %s AND strike_price = %s AND option_type = %s
                    """, (ticker_id, next_exp, strike, option_type.upper()))
                    option_entry = cursor.fetchone()
                    if not option_entry:
                        cursor.execute("""
                            INSERT INTO options (ticker_id, expiration_date, strike_price, option_type)
                            VALUES (%s, %s, %s, %s)
                        """, (ticker_id, next_exp, strike, option_type.upper()))
                        option_id = cursor.lastrowid
                    else:
                        option_id = option_entry['id']

                    # Prepare data for bulk insert
                    data_to_insert.append((
                        option_id, today, open_price, high_price, low_price, close_price, volume
                    ))

                    print(f"Prepared {symbol}")

            except Exception as e:
                print(f"Error processing {ticker}: {e}")

        # Bulk insert
        if data_to_insert:
            insert_query = """
                INSERT INTO option_prices (option_id, date_collected, open_price, high_price, low_price, end_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    open_price=VALUES(open_price),
                    high_price=VALUES(high_price),
                    low_price=VALUES(low_price),
                    end_price=VALUES(end_price),
                    volume=VALUES(volume)
            """
            cursor.executemany(insert_query, data_to_insert)
            print(f"Inserted {len(data_to_insert)} option price records.")

if __name__ == "__main__":
    tickers_to_fetch = []
    all_biotech_tickers = getBioTickers.scrape_biotech_tickers("https://stockanalysis.com/stocks/industry/biotechnology/")
    scraped_tickers = scraper.scrape_tickers(["https://www.barchart.com/options/income-strategies/naked-puts?orderBy=potentialReturn&orderDir=desc"])
    for ticker in scraped_tickers:
        if ticker in all_biotech_tickers:
            tickers_to_fetch.append(ticker)
    print(f"found {len(tickers_to_fetch)} biotech tickers to fetch.")
    fetch_and_store(tickers_to_fetch)
