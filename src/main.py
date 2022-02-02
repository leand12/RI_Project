# Bruno Bastos 93302
# Leandro Silva 93446

import os
import sys
import logging
import coloredlogs
import argparse
from tokenizer import Tokenizer
from indexer import Indexer
from query import Query
import time

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='DEBUG', logger=logger)
coloredlogs.install(
    level='DEBUG', logger=logger, datefmt='%H:%M:%S',
    fmt='\33[1m\33[34m%(filename)s:%(lineno)d %(asctime)s\33[0m - %(message)s'
)


def create_indexer(args):
    if args.config:
        indexer = Indexer.read_config(args.config)
    else:
        args_dict = vars(args)
        tokenizer = Tokenizer(**args_dict)
        indexer = Indexer(tokenizer=tokenizer, **args_dict)

    start = time.perf_counter()
    indexer.index_file(args.index)
    logging.info(
        f"Finished indexing ({time.perf_counter() - start:.2f} seconds)")
    logging.info(f"Vocabulary size: {indexer.vocabulary_size}")
    logging.info(f"Index size on disk: {indexer.disk_size}")
    logging.info(f"Index segments written to disk: {indexer.num_segments}")


def search_indexer(args):
    start = time.perf_counter()
    indexer = Indexer.load_metadata(args.search)

    logging.info(
        f"Time taken to start up index: {time.perf_counter() - start:.2f} seconds")

    query = Query(indexer)

    if args.test:
        query.search_file_with_accuracy("queries.relevance.txt", args.boost)

    elif args.query:
        query.search_file(args.query, args.boost)

    else:
        while True:
            try:
                search = input("Search: ")
            except EOFError:
                # quit on CTRL+D
                print()
                break

            start = time.perf_counter()
            results = query.search(search, args.boost)

            if results:
                logging.info(
                    f"{len(results)} results ({time.perf_counter() - start:.2f} seconds)")
                logging.info(results)
            else:
                logging.info(
                    f"Your search - {search} - did not match any documents")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Document indexer using the SPIMI approach')

    subparser = parser.add_subparsers(
        title='mode argument', dest='mode', required=True, help='mode of the program')

    d_parser = subparser.add_parser('index',
                                    help='create an indexer with the configurations provided')
    d_parser.add_argument('index', metavar='FILE',
                          help='file with the documents to index')
    d_parser.add_argument('-c', '--config', metavar='FILE',
                          help='json file with configurations to build the indexer '
                          '(additional options will be ignored)')

    group1 = d_parser.add_argument_group('indexer optional arguments')
    group1.add_argument('--positional', action='store_true',
                        help='save the terms\' positions in a document')
    group1.add_argument('--save-zip', action='store_true',
                        help='zip the output files of the indexer')
    group1.add_argument('--doc-rename', action='store_true',
                        help='rename document IDs for a more efficient space usage')
    group1.add_argument('--file-location-step', metavar='STEP', type=int, nargs='?', default=1, const=0,
                        help='store file location for terms step by step (const: %(const)s, default: %(default)s)')
    group1.add_argument('--block-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                        help='maximum number of documents that can be stored in a block (default: %(default)s)')
    group1.add_argument('--merge-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                        help='maximum number of documents that can be stored in a index (default: %(default)s)')
    group1.add_argument('--merge-chunk-size', metavar='SIZE', type=int, default=1000,
                        help='size of the block chunks read (default: %(default)s)')
    group1.add_argument('--merge-dir', metavar='DIR', default="indexer/",
                        help='source directory path to store the indexer (default: %(default)s)')

    group2 = d_parser.add_argument_group('tokenizer optional arguments')
    group2.add_argument('--case-folding', action='store_true',
                        help='convert every token to lowercase')
    group2.add_argument('--no-numbers', action='store_true',
                        help='remove tokens with only numbers')
    group2.add_argument('--stemmer', action='store_true',
                        help='stemmerize the tokens')
    group2.add_argument('--min-length', metavar='LENGTH', type=int, default=3,
                        help='remove tokens with lower minimum length (default: %(default)s)')
    group2.add_argument('--stopwords-file', metavar='FILE', default="../data/nltk_en_stopwords.txt",
                        help='remove tokens from a stopwords file (default: %(default)s)')
    group2.add_argument('--contractions-file', metavar='FILE', default="../data/en_contractions.txt",
                        help='replace tokens from a contractions file (default: %(default)s)')

    group3 = d_parser.add_argument_group('ranking optional arguments')
    group3.add_argument('-n, --name', choices=['VSM', 'BM25'], default="BM25",
                        help='the type of ranking (default: %(default)s)')
    group3.add_argument('-p1', metavar='SCHEME', type=str, default="lnc",
                        help='document scheme (default: %(default)s)')
    group3.add_argument('-p2', metavar='SCHEME', type=str, default="ltc",
                        help='query scheme (default: %(default)s)')
    group3.add_argument('-k1', metavar='N', type=float, default=1.2,
                        help='term frequency scaling (default: %(default)s)')
    group3.add_argument('-b', metavar='N', type=float, default=1,
                        help='document length normalization (default: %(default)s)')

    i_parser = subparser.add_parser('search',
                                    help='search in an indexer already created')
    i_parser.add_argument('search', metavar='DIR',
                          help='source directory of an indexer')
    i_parser.add_argument('-b', '--boost', action='store_true',
                          help='boost query results with a function that ranks according to document windows')
    i_group = i_parser.add_mutually_exclusive_group()
    i_group.add_argument('-q', '--query', metavar='FILE',
                          help='text file with multiple queries separated by a new line')
    i_group.add_argument('-t', '--test', action='store_true',
                          help='test results accuracy comparing with scores from \"queries.relevance.txt\"')

    args = parser.parse_args()

    if args.mode == 'index':
        create_indexer(args)
    elif args.mode == 'search':
        search_indexer(args)
