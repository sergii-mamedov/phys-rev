# v. 1.2
# 07.09.2017
# Sergii Mamedov

"""
Gevent version.
Get metadata from all dois from a journal.
Journal`s urls: https://www.crossref.org/06members/51depositor.html
"""

import time
import json
import logging
import argparse

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
    return {'PhysRevX.01': list, 'PhysRevX.02': list}
    """

    data = {}
    for item in sequence:
        key = item.split('.')
        key = '{}.{}'.format('.'.join(key[:2]), key[2].zfill(3))
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

    parser = argparse.ArgumentParser()
    parser.description = ('Get metadata from all dois from a journals of APS')
    parser.add_argument('-t', '--thread', default=10, type=int, 
                        help='number of thread, max - 10, defaul - 10')
    parser.add_argument('-j', '--journal', help='name of a journal')
    args = parser.parse_args()

    journals = {'Phys. Rev. A': 'http://data.crossref.org/depositorreport?pubid=J5203',
                'Phys. Rev. B': 'http://data.crossref.org/depositorreport?pubid=J5200',
                'Phys. Rev. C': 'http://data.crossref.org/depositorreport?pubid=J5201',
                'Phys. Rev. D': 'http://data.crossref.org/depositorreport?pubid=J5199',
                'Phys. Rev. E': 'http://data.crossref.org/depositorreport?pubid=J5202',
                'Phys. Rev. X': 'http://data.crossref.org/depositorreport?pubid=J140965',
                'Phys. Rev. Lett': 'http://data.crossref.org/depositorreport?pubid=J5204'}

    thread = args.thread
    if thread > 10 or thread < 1:
        thread = 10

    if args.journal == 'all':
        pass
    elif args.journal in journals:
        journals = {args.journal: journals.get(args.journal)}
    else:
        print('Available journals: \n\n{}'.format('; '.join(journals.keys())))
        return

    for journal, url in journals.items():
        logging.info('Start {}'.format(journal))
        dois = get_dois_list(url)
        dois = change_dois_list(dois)
        logging.info('Get DOIs list')

        pool = gevent.pool.Pool(thread)
        for name, dois_sublist in tqdm(sorted(dois.items(), key=lambda x: x)):
            pool.wait_available()
            pool.apply_async(get_info, args=[name, dois_sublist])
        pool.join()

if __name__ == '__main__':
    main()
