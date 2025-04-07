import datetime
import pymysql
import yfinance as yf

# MySQL database settings
#need to update
DB_HOST = 'your_mysql_host'
DB_PORT = 3306
DB_USER = 'your_mysql_user'
DB_PASSWORD = 'your_mysql_password'
DB_NAME = 'your_database_name'

# Connect to MySQL
connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    port=DB_PORT,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def fetch_and_store_option_data(option_symbols):
    today = datetime.date.today()

    with connection.cursor() as cursor:
        for option_symbol in option_symbols:
            try:
                option_data = yf.Ticker(option_symbol)
                hist = option_data.history(period="1d")
                if hist.empty:
                    print(f"No data for {option_symbol}")
                    continue

                row = hist.iloc[-1]
                open_price = row['Open']
                high_price = row['High']
                low_price = row['Low']
                close_price = row['Close']
                volume = row['Volume']

                # Parse the option symbol
                underlying_symbol = ''.join(filter(str.isalpha, option_symbol))
                if underlying_symbol.endswith('C') or underlying_symbol.endswith('P'):
                    underlying_symbol = underlying_symbol[:-1]

                expiration_date = datetime.datetime.strptime(option_symbol[len(underlying_symbol):len(underlying_symbol)+6], '%y%m%d').date()
                call_put = 'CALL' if 'C' in option_symbol else 'PUT'
                strike_raw = option_symbol.split(call_put[0])[1]
                strike_price = int(strike_raw) / 1000

                # Ensure Ticker exists
                cursor.execute("SELECT id FROM tickers WHERE symbol = %s", (underlying_symbol,))
                ticker = cursor.fetchone()
                if not ticker:
                    cursor.execute("INSERT INTO tickers (symbol) VALUES (%s)", (underlying_symbol,))
                    ticker_id = cursor.lastrowid
                else:
                    ticker_id = ticker['id']

                # Ensure Option exists
                cursor.execute("""
                    SELECT id FROM options
                    WHERE ticker_id = %s AND expiration_date = %s AND strike_price = %s AND option_type = %s
                """, (ticker_id, expiration_date, strike_price, call_put))
                option = cursor.fetchone()
                if not option:
                    cursor.execute("""
                        INSERT INTO options (ticker_id, expiration_date, strike_price, option_type)
                        VALUES (%s, %s, %s, %s)
                    """, (ticker_id, expiration_date, strike_price, call_put))
                    option_id = cursor.lastrowid
                else:
                    option_id = option['id']

                # Insert or Update OptionPrice
                cursor.execute("""
                    SELECT id FROM option_prices
                    WHERE option_id = %s AND date_collected = %s
                """, (option_id, today))
                price = cursor.fetchone()
                if price:
                    cursor.execute("""
                        UPDATE option_prices
                        SET open_price = %s, high_price = %s, low_price = %s, end_price = %s, volume = %s
                        WHERE id = %s
                    """, (open_price, high_price, low_price, close_price, volume, price['id']))
                else:
                    cursor.execute("""
                        INSERT INTO option_prices (option_id, date_collected, open_price, high_price, low_price, end_price, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (option_id, today, open_price, high_price, low_price, close_price, volume))

                print(f"Stored data for {option_symbol}")

            except Exception as e:
                print(f"Error processing {option_symbol}: {e}")

if __name__ == "__main__":
    options_to_fetch = [
        "AAPL240419C00180000",
        "SPY240419P00450000",
        # add more options here
    ]
    fetch_and_store_option_data(options_to_fetch)
