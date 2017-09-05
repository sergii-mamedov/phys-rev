# v. 1.1
# 04.09.2017
# Sergii Mamedov

"""
Gevent version.
Get metadata from all dois from a journal.
Journal`s urls: https://www.crossref.org/06members/51depositor.html
"""

import time
import json
import logging

import requests
from tqdm import tqdm

import gevent
from gevent import monkey

# https://github.com/tqdm/tqdm/issues/404
gevent.monkey.patch_all(thread=False)
OUTPUT_LOCK = gevent.lock.Semaphore()

FORMAT = '%(asctime)s   %(levelname)s   %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

URL_API = 'http://api.crossref.org/works/'
URL_JOURNAL = 'http://data.crossref.org/depositorreport?pubid=J5202'


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
            logging.info('RequestException\t{}'.format(err))

        time.sleep(MAX_RETRIES)

    return html


def get_dois_list(url):
    """
    return all dois from journals
    """

    raw = connect_get(url, timeout=120)
    return [item.split(' ')[0] for item in raw.split('\r\n')[2:] if item.strip()]


def change_dois_list(sequence):
    """
    """

    data = {}
    for item in sequence:
        key = item.split('.')
        key = '{}.{}'.format('.'.join(key[:2]), key[2].zfill(2))
        data[key] = data.get(key, []) + [item]

    return data


def get_info(name, dois):
    """
    write metadata of article in file
    """

    name = name.split('/')[1].split('.')
    name = '{}.{}.txt'.format(name[0], name[1])
    with open(name, encoding='utf-8', mode='w') as f:
        for doi in dois:
            item = connect_get(URL_API+doi)
            item = json.loads(item)
            if item.get('message') and item['message'].get('type') \
               and item['message']['type'] == 'journal-article':
                f.write(json.dumps(item, ensure_ascii=False) + '\n')


def main():

    logging.info('Start')
    dois = get_dois_list(URL_JOURNAL)
    dois = change_dois_list(dois)
    logging.info('Get DOIs list')

    pool = gevent.pool.Pool(10)
    for name, dois_sublist in tqdm(sorted(dois.items(), key=lambda x: x)):
        pool.wait_available()
        pool.apply_async(get_info, args=[name, dois_sublist])
    pool.join()

if __name__ == '__main__':
    main()

