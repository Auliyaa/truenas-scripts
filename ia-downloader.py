import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse, unquote
from tqdm import tqdm
import os
import sys
import time

def parse_args():
    parser = argparse.ArgumentParser(description="Parse cookie values from command line arguments.")
    parser.add_argument('--username', type=str, required=True, 
                        help="archive.org username")
    parser.add_argument('--password', type=str, required=True, 
                        help="archive.org password")
    parser.add_argument('--page-id', type=str, required=True, 
                        help="Root page id to parse")
    parser.add_argument('--ext', type=str, required=False, 
                        help="Filter file extensions")
    return parser.parse_args()


BASE_URL = "https://archive.org"
LOGIN_URL = f"{BASE_URL}/account/login"
DOWNLOAD_URL = f"{BASE_URL}/download"
RETRY_DELAY = 120
REQUEST_TIMEOUT = 60

session = requests.Session()
# session_headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0'
# }

def login(username: str, password: str):
    session = requests.Session()
    # session.headers = session_headers
    response = session.get(LOGIN_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    login_data = {
        'username': username,
        'password': password,
        'referer': 'https://archive.org/',
        'remember': True,
        'login': True,
        'submit_by_js': True
    }
    login_response = session.post(LOGIN_URL, data=login_data)
    if login_response.status_code != 200:
        print(login_response.text)

    return login_response.status_code == 200

def download(url: str, out_file: str):
    with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        if response.status_code != 200:
            print(response.text)
            return False            

        total_sz = int(response.headers.get("content-length", 0))
        with open(out_file, "wb") as fd:
            with tqdm(total=total_sz, unit="B", unit_scale=True, desc=out_file) as progress_bar:
                for chunk in response.iter_content(chunk_size=1024):
                    fd.write(chunk)
                    progress_bar.update(len(chunk))
    return True


def main():
    args = parse_args()
    print(".. logging-in")
    if not login(username=args.username, password=args.password):
        print("!! login failed")
        sys.exit(1)
    print("  loggin success")
    
    print(".. fetching download page")
    dl_url_base = f"{DOWNLOAD_URL}/{args.page_id}"
    response = session.get(url=dl_url_base, timeout=REQUEST_TIMEOUT)
    # print(response.text)

    if response.status_code != 200:
        sys.exit(1)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    dl_links = soup.find_all('a')
    if args.ext:
        href_values = [dl_url_base + "/" + link['href'] for link in dl_links if 'href' in link and link['href'].endswith(args.ext)]
    else:
        href_values = [dl_url_base + "/" + link['href'] for link in dl_links if 'href' in link]
    
    for href_value in href_values:
        file_name = os.path.basename(unquote(urlparse(href_value).path))
        print(f".. {href_value} -> {file_name}")
        try:
            if not download(url=href_value, out_file=file_name):
                raise RuntimeError("")
            else:
                print(f" downloaded {href_value} -> {file_name}")
        except Exception as e:
            print(f"!! failed to download url: {href_value}. retying in {RETRY_DELAY}secs")
            time.sleep(RETRY_DELAY)

            print(".. logging-in")
            if not login(username=args.username, password=args.password):
                print("!! login failed")
                sys.exit(1)
            print("  loggin success")

            if not download(url=href_value, out_file=file_name):
                print(f"!! failed to download url: {href_value}.")
            else:
                print(f" downloaded {href_value} -> {file_name}")

if __name__ == "__main__":
    main()
    