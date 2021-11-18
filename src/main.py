import os
import logging
import coloredlogs
import argparse
from tokenizer import Tokenizer
from indexer import Indexer
from query import Query
from timeit import default_timer as timer


logger = logging.getLogger(__name__)  # get a specific logger object
coloredlogs.install(level='DEBUG')  # install a handler on the root logger with level debug
coloredlogs.install(level='DEBUG', logger=logger)  # pass a specific logger object
coloredlogs.install(
    level='DEBUG', logger=logger, datefmt='%H:%M:%S',
    fmt='\33[1m\33[34m%(filename)s:%(lineno)d %(asctime)s\33[0m - %(message)s'
)


parser = argparse.ArgumentParser(
    usage="main.py [-h] (-d FILE | -i DIR) [OPTIONS ...]",
    description='Document indexer using the SPIMI approach')

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-d', '--dataset', metavar='FILE',
                   help='file with the documents to index')
group.add_argument('-i', '--indexer', metavar='DIR',
                   help='source directory of a indexer')

group1 = parser.add_argument_group('indexer optional arguments')
group1.add_argument('--positional', action='store_true',
                    help='save the terms\' positions in a document')
group1.add_argument('--save-zip', action='store_true',
                    help='')
group1.add_argument('--doc-rename', action='store_true',
                    help='')
group1.add_argument('--file-location', action='store_true',
                    help='')
group1.add_argument('--file-location-step', metavar='STEP', type=int, default=100,
                    help='')
group1.add_argument('--block-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                    help='')
group1.add_argument('--merge-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                    help='')
group1.add_argument('--merge-chunk-size', metavar='SIZE', type=int, default=1000,
                    help='')
group1.add_argument('--block-dir', metavar='DIR', default="block/",
                    help='')
group1.add_argument('--merge-dir', metavar='DIR', default="indexer/",
                    help='')

group2 = parser.add_argument_group('tokenizer optional arguments')
group2.add_argument('--case-folding', action='store_true',
                    help='')
group2.add_argument('--no-numbers', action='store_true',
                    help='')
group2.add_argument('--stemmer', action='store_true',
                    help='')
group2.add_argument('--min-length', metavar='LENGTH', type=int, default=3,
                    help='')
group2.add_argument('--stopwords-file', metavar='FILE', default="../data/nltk_en_stopwords.txt",
                    help='')
group2.add_argument('--contractions-file', metavar='FILE', default="../data/en_contractions.txt",
                    help='')

args = vars(parser.parse_args())

if __name__ == "__main__":
    tokenizer = Tokenizer(**args)
    indexer = Indexer(**args)

    start = timer()
    indexer.index_file(args["dataset"])
    logging.info(f"Finished indexing ({timer() - start:.2f} seconds)")
    logging.info(f"Vocabulary size: {indexer.vocabulary_size}")
    logging.info(f"Index size on disk: {indexer.disk_size}")
    logging.info(f"Index segments written to disk: {indexer.num_segments}")

    exit()

    query = Query(indexer)

    search = input("Search: ")

    start = timer()
    results = query.search(search)

    if results:
        logging.info(
            f"{len(results)} results ({timer() - start:.2f} seconds)")
    else:
        logging.info(f"Your search - {search} - did not match any documents")


"""

index para os ficheiros gerados, com steps e usar binary search

"""
