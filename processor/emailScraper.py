import imaplib
import email
from bs4 import BeautifulSoup
import os
import re

# Email credentials from environment variables
EMAIL_USER = os.environ.get('EMAIL_USERNAME')
EMAIL_PASS = os.environ.get('EMAIL_PASSWORD')
EMAIL_SERVER = os.environ.get('EMAIL_SERVER', 'imap.gmail.com')
EMAIL_FOLDER = os.environ.get('EMAIL_FOLDER', 'INBOX')

def extract_tickers_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tickers = set()

    # Look for anchor tags pointing to barchart.com/quotes/
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(r'barchart\.com/quotes/([A-Z]+)', href)
        if match:
            tickers.add(match.group(1))

    return list(tickers)

def scrape_emails():
    """Connects to email server, fetches messages, extracts tickers from content."""
    tickers = set()

    try:
        mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select(EMAIL_FOLDER)

        # Search for all emails
        result, data = mail.search(None, 'ALL')
        if result != 'OK':
            print("No messages found!")
            return []

        email_ids = data[0].split()

        for e_id in email_ids[-10:]:  # check the last 10 emails
            result, data = mail.fetch(e_id, '(RFC822)')
            if result != 'OK':
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_body = part.get_payload(decode=True).decode()
                    extracted = extract_tickers_from_html(html_body)
                    tickers.update(extracted)

    except Exception as e:
        print(f"Error fetching emails: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

    return list(tickers)


if __name__ == "__main__":
    tickers = scrape_emails()
    print("Final ticker list from emails:", tickers)