# <a href="https://dblp.org/rec/conf/cvpr/KlingnerBMF21.html?view=bibtex"><img alt="" src="https://dblp.org/img/download.dark.hollow.16x16.png" class="icon"></a>
# https://dblp.org/rec/conf/cvpr/KlingnerBMF21.bib?param=1

import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import argparse
import os


BASE_URL = "https://dblp.org/db/conf/{}/index.html"


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
                response = requests.get(tmp.split('.html')[0] + '.bib?param=1')
                bib_list.append(response.content)
                itr += 1
    print(f"[*] retrieved {itr} items")
    return bib_list


def save_bib_list(bib_list, conf_name):
    with open('raw_data/' + conf_name + '.bib', 'w') as f:
        for bib in bib_list:
            f.write(bib.decode("utf-8"))


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
        bib_list = get_bib_list(url)
        save_bib_list(bib_list, name)
        os.system(f"python bib2json.py -i raw_data/{name}.bib -o data/{name}.bib.json")
        with open('bib_list.txt', 'a') as f:
            f.write(f"data/{name}.bib.json\n")
    print("[*] done")

    # bib_list = get_bib_list('https://dblp.org/db/conf/cvpr/cvprw2021.html')
    # save_bib_list(bib_list, 'cvprw', '2021')

