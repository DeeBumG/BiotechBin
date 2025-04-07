from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def scrape_tickers(urls):
    """
    Scrape unique ticker symbols from a list of URLs and return them.
    
    Args:
        urls (list): List of URLs to scrape tickers from.
    
    Returns:
        list: List of unique ticker symbols.
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,5000")  # Set a visible window size

    # Set up service with webdriver-manager
    service = Service(ChromeDriverManager().install())

    driver = None
    all_tickers = set()

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        for url in urls:
            print(f"Scraping {url}...")
            driver.get(url)
            
            tickers = driver.execute_script("""
                const shadow = document.querySelector('bc-data-grid').shadowRoot;
                const links = shadow.querySelectorAll('a[href*="/stocks/quotes/"]');
                const uniqueTickers = new Set(Array.from(links).map(link => {
                    const parts = link.href.split('/');
                    return parts[parts.indexOf('quotes') + 1];
                }));
                return Array.from(uniqueTickers);
            """)

            all_tickers.update(tickers)
            print(f"Found {len(tickers)} tickers from {url}")

        ticker_list = sorted(list(all_tickers))
        
        if ticker_list:
            print(f"Total unique tickers found: {len(ticker_list)}")
            with open('tickers.txt', 'w') as f:
                f.write('\n'.join(ticker_list))
            print("All tickers saved to 'tickers.txt'")
        else:
            print("No tickers found across all URLs")

        return ticker_list

    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        if driver is not None:
            driver.quit()

#Example usage
if __name__ == "__main__":
    url_list = [
        "https://www.barchart.com/options/income-strategies/naked-puts?orderBy=potentialReturn&orderDir=desc"
    ]
    tickers = scrape_tickers(url_list)
    print("Final ticker list:", tickers)