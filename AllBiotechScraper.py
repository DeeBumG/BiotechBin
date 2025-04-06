import requests
from bs4 import BeautifulSoup

# Headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_biotech_tickers(url):
    """
    Scrape ticker symbols from the biotechnology industry page on StockAnalysis.com.
    Returns a list of all biotech tickers.
    """
    try:
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table containing the stock data (class may have changed; using a broader approach)
        table = soup.find('table')
        if not table:
            raise ValueError("Could not find the stock table on the page")

        # Extract tickers from the table rows
        tickers = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) > 1:  # Ensure row has enough cells
                # Ticker is in the second column (index 1), inside an <a> tag
                ticker_link = cells[1].find('a')
                if ticker_link:
                    ticker = ticker_link.text.strip()
                    tickers.append(ticker)

        return tickers

    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except ValueError as e:
        print(f"Error parsing the page: {e}")
        return []

def write_dictionary_to_file(biostocks, filename="biotickers.txt"):
    """
    Write the list to a text file in the specified format.
    """
    with open(filename, 'w') as f:
        for ticker in (biostocks):
            f.write(f"{ticker},")
    print(f"List written to {filename}")
    print(f"Total tickers scraped: {len(biostocks)}")

# URL to scrape
url = "https://stockanalysis.com/stocks/industry/biotechnology/"

# Scrape the tickers and create the dictionary
biostocks = scrape_biotech_tickers(url)

# Write the dictionary to a file if scraping was successful
if biostocks:
    write_dictionary_to_file(biostocks)
else:
    print("No tickers were scraped. Check the URL or page structure.")