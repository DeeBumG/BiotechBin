import os
import datetime
import pymysql
import requests
import getBioTickers
import emailScraper

# MySQL connection
DB_HOST = os.environ.get('DATABASE_HOST')
DB_PORT = int(os.environ.get('DATABASE_PORT', 3306))
DB_USER = os.environ.get('DATABASE_USER')
DB_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DB_NAME = os.environ.get('DATABASE_NAME')

TRADIER_API_KEY = os.environ.get('TRADIER_API_KEY')  # Your Tradier API Key
TRADIER_ENDPOINT = "https://api.tradier.com/v1"

HEADERS = {
    "Authorization": f"Bearer {TRADIER_API_KEY}",
    "Accept": "application/json"
}

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
    return f"{int(strike * 1000):08d}"

def build_option_symbol(ticker, exp_date, option_type, strike):
    date_part = exp_date.strftime('%y%m%d')
    type_letter = 'C' if option_type == 'call' else 'P'
    strike_part = format_strike_price(strike)
    return f"{ticker}{date_part}{type_letter}{strike_part}"

def fetch_expirations(ticker):
    url = f"{TRADIER_ENDPOINT}/markets/options/expirations"
    params = {"symbol": ticker, "includeAllRoots": "true", "strikes": "false"}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    expirations = resp.json().get("expirations", {}).get("date", [])
    return expirations

def fetch_option_chain(ticker, expiration_date):
    url = f"{TRADIER_ENDPOINT}/markets/options/chains"
    params = {"symbol": ticker, "expiration": expiration_date}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    options = resp.json().get("options", {}).get("option", [])
    return options

def fetch_quote(symbol):
    url = f"{TRADIER_ENDPOINT}/markets/quotes"
    params = {"symbols": symbol}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json().get("quotes", {}).get("quote", {})

def fetch_and_store(tickers):
    today = datetime.date.today()
    data_to_insert = []

    with connection.cursor() as cursor:
        for ticker in tickers:
            try:
                expirations = fetch_expirations(ticker)
                if not expirations:
                    print(f"No expirations found for {ticker}")
                    continue

                next_exp = expirations[0]  # soonest expiration
                options = fetch_option_chain(ticker, next_exp)

                calls = [opt for opt in options if opt['option_type'] == 'call']
                puts = [opt for opt in options if opt['option_type'] == 'put']

                calls_sorted = sorted(calls, key=lambda x: x.get('volume', 0), reverse=True)[:2]
                puts_sorted = sorted(puts, key=lambda x: x.get('volume', 0), reverse=True)[:2]

                all_options = [(opt, 'call') for opt in calls_sorted] + [(opt, 'put') for opt in puts_sorted]

                for option_data, option_type in all_options:
                    strike = option_data['strike']
                    symbol = build_option_symbol(ticker, datetime.datetime.strptime(next_exp, '%Y-%m-%d'), option_type, strike)

                    quote = fetch_quote(symbol)
                    if not quote or 'last' not in quote:
                        print(f"No quote data for {symbol}")
                        continue
                
                    open_price = quote.get('open', 0)
                    high_price = quote.get('high', 0)
                    low_price = quote.get('low', 0)
                    close_price = quote.get('last', 0)
                    volume = quote.get('volume', 0)

                    if None in (open_price, high_price, low_price, close_price, volume):
                        print(f"Skipping {symbol} due to missing quote data.")
                        continue

                    # Insert ticker
                    cursor.execute("SELECT id FROM tickers WHERE symbol = %s", (ticker,))
                    ticker_row = cursor.fetchone()
                    if not ticker_row:
                        cursor.execute("INSERT INTO tickers (symbol) VALUES (%s)", (ticker,))
                        ticker_id = cursor.lastrowid
                    else:
                        ticker_id = ticker_row['id']

                    # Insert option
                    cursor.execute("""
                        SELECT id FROM options
                        WHERE ticker_id = %s AND expiration_date = %s AND strike_price = %s AND option_type = %s
                    """, (ticker_id, next_exp, strike, option_type.upper()))
                    option_row = cursor.fetchone()
                    if not option_row:
                        cursor.execute("""
                            INSERT INTO options (ticker_id, expiration_date, strike_price, option_type)
                            VALUES (%s, %s, %s, %s)
                        """, (ticker_id, next_exp, strike, option_type.upper()))
                        option_id = cursor.lastrowid
                    else:
                        option_id = option_row['id']

                    data_to_insert.append((
                        option_id, today, open_price, high_price, low_price, close_price, volume
                    ))

                    print(f"Prepared {symbol}")
                    print(f"{option_id}, {today}, {open_price}, {high_price}, {low_price}, {close_price}, {volume}")

            except Exception as e:
                print(f"Error processing {ticker}: {e}")

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
    scraped_tickers = emailScraper.scrape_emails()
    for ticker in scraped_tickers:
        if ticker in all_biotech_tickers:
            tickers_to_fetch.append(ticker)
    print(f"found {len(tickers_to_fetch)} biotech tickers to fetch.")
    fetch_and_store(tickers_to_fetch)

