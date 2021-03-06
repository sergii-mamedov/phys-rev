# v. 1.1
# 03.09.2017
# Sergii Mamedov

"""
Requests version.
Get metadata from all dois from a journal.
Journal`s urls: https://www.crossref.org/06members/51depositor.html
"""

import time
import json
import logging

from tqdm import tqdm
import requests

FORMAT = '%(asctime)s   %(levelname)s   %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


def connect_get(url, timeout=30, headers={}, cookies={}):
    """
    get source code from page
    """

    MAX_RETRIES = 5

    for i in range(0, MAX_RETRIES):
        html = u''
        try:
            conn = requests.get(url, timeout=timeout, headers=headers, cookies=cookies, verify=False)
            html = conn.text
            conn.raise_for_status()
            break
        except requests.exceptions.RequestException as err:
            logging.info('RequestException, HTTP Code\t{}'.format(conn.status_code))

        time.sleep(1.0)

    return html


def get_dois_list(url):
    """
    get all dois from journals
    """

    raw = connect_get(url, timeout=120)
    return [item.split(' ')[0] for item in raw.split('\r\n')[2:] if item.strip()]


def main():

    URL_API = 'http://api.crossref.org/works/'
    URL_JOURNAL = 'http://data.crossref.org/depositorreport?pubid=J140965'

    dois = get_dois_list(URL_JOURNAL)

    for doi in tqdm(dois):
        item = connect_get(URL_API+doi)
        item = json.loads(item)
        if item.get('message') and item['message'].get('type') \
           and item['message']['type'] == 'journal-article':
            print(json.dumps(item, ensure_ascii=False))

if __name__ == '__main__':
    main()
