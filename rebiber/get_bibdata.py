# <a href="https://dblp.org/rec/conf/cvpr/KlingnerBMF21.html?view=bibtex"><img alt="" src="https://dblp.org/img/download.dark.hollow.16x16.png" class="icon"></a>
# https://dblp.org/rec/conf/cvpr/KlingnerBMF21.bib?param=1

import requests
from bs4 import BeautifulSoup
import argparse
import os
from requests.sessions import Session
import time
from concurrent.futures import ThreadPoolExecutor
from threading import local
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["GET",]
)
adapter = HTTPAdapter(max_retries=retry_strategy)


BASE_URL = "https://dblp.org/db/conf/{}/index.html"
thread_local = local()


def get_conf_list(conf_name):
    response = requests.get(BASE_URL.format(conf_name))
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find_all('ul', class_='publ-list')

    conf_list = []
    for item in items:
        links = item.find_all('a')
        tmp = ""
        for link in links:
            if tmp == link.get('href'):
                continue
            if "/db/" in link.get('href'):
                tmp = link.get('href')
                conf_list.append(tmp)
    return conf_list


def get_bib_list(conf_url):
    response = requests.get(conf_url)
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find_all('ul', class_='publ-list')

    bib_list = []
    itr = 0
    for item in items:
        links = item.find_all('a')
        tmp = ""
        for link in links:
            if tmp == link.get('href'):
                continue
            if "bibtex" in link.get('href'):
                tmp = link.get('href')
                print(tmp)
                bib_list.append(tmp.split('.html')[0] + '.bib?param=1')
                itr += 1
    print(f"[*] retrieved {itr} items")
    download_all(bib_list)
    return bib_list


def get_session() -> Session:
    if not hasattr(thread_local,'session'):
        thread_local.session = requests.Session()
    return thread_local.session


def download_link(url:str):
    session = get_session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    with session.get(url) as response:
        if response.status_code == 200:
            with open('raw_data/' + 'tmp.bib', 'a') as f:
                f.write(response.content.decode("utf-8"))
            time.sleep(0.1)
        else:
            print(f"[*] {url} failed with status code: {response.status_code}")


def download_all(url_list) -> None:
    print("[*] downloading bibtex files")
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(download_link, url_list)


def save_bib_list(conf_name):
    os.rename('raw_data/' + 'tmp.bib', 'raw_data/' + conf_name + '.bib')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get bibtex data from dblp')
    parser.add_argument('--conf', type=str, help='conference name')
    parser.add_argument('--year', type=str, help='conference year')
    args = parser.parse_args()

    conf_url = get_conf_list(args.conf)
    urls = {}
    for url in conf_url:
        if args.year in url:
            urls[str(url).split("/")[-1].split(".")[0]] = url

    if not urls:
        print("[!] No conference found in https://dblp.org/db/conf/index.html")
        exit(1)

    for name, url in urls.items():
        print(f"[*] retrieving {name}")
        get_bib_list(url)
        save_bib_list(name)
        os.system(f"python bib2json.py -i raw_data/{name}.bib -o data/{name}.bib.json")
        with open('bib_list.txt', 'a') as f:
            f.write(f"data/{name}.bib.json\n")
    print("[*] done")