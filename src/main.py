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
    indexer.index_file(args.dataset)
    logging.info(
        f"Finished indexing ({time.perf_counter() - start:.2f} seconds)")
    logging.info(f"Vocabulary size: {indexer.vocabulary_size}")
    logging.info(f"Index size on disk: {indexer.disk_size}")
    logging.info(f"Index segments written to disk: {indexer.num_segments}")


def init_indexer(args):
    start = time.perf_counter()
    indexer = Indexer.load_metadata(args.indexer)

    # indexer.idf_score()
    logging.info(
        f"Time taken to start up index: {time.perf_counter() - start:.2f} seconds")

    if args.search:
        # TODO: count times for each query, and maybe store them
        query.search_file("queries.txt")

    else:
        while True:
            query = Query(indexer)

            try:
                search = input("Search: ")
            except EOFError:
                # quit on CTRL+D
                break

            start = time.perf_counter()
            results = query.search(search)

            if results:
                logging.info(
                    f"{len(results)} results ({time.perf_counter() - start:.2f} seconds)")
                logging.info(results)
            else:
                logging.info(
                    f"Your search - {search} - did not match any documents")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        add_help=False,
        usage="main.py [-h [{dataset,indexer}]] (-d FILE | -i DIR) [OPTIONS ...]",
        description='Document indexer using the SPIMI approach')

    parser.add_argument('-h', '--help', nargs='?', choices=['dataset', 'indexer'],
                        help='show this message and exit')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--dataset', metavar='FILE',
                       help='create indexer from a file with the documents to index')
    group.add_argument('-i', '--indexer', metavar='DIR',
                       help='initialize indexer from a source directory of a indexer')

    # if len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help'):
    #     parser.print_help()
    #     exit(0)

    args, unknown = parser.parse_known_args()

    print(args.help)

    if args.help:
        parser.print_help()
        exit(0)

    if args.dataset or args.help == 'dataset':
        parser.add_argument('-c', '--config', metavar='FILE',
                            help='json file with the configurations to build the tokenizer and indexer'
                            '(additional options will be ignored)')

        group1 = parser.add_argument_group('indexer optional arguments')
        group1.add_argument('--positional', action='store_true',
                            help='save the terms\' positions in a document')
        group1.add_argument('--save-zip', action='store_true',
                            help='zip the output files of the indexer')
        group1.add_argument('--doc-rename', action='store_true',
                            help='rename document IDs for a more efficient space usage')
        # FIXME: nargs='?'
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

        group2 = parser.add_argument_group('tokenizer optional arguments')
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

        if args.help == 'dataset':
            parser.print_help()
            exit(0)

        args = parser.parse_args()
        create_indexer(args)

    elif args.indexer or args.help == 'indexer':

        parser.add_argument('-s', '--search', metavar='FILE',
                            help='text file with multiple queries separated by a new line')

        group3 = parser.add_argument_group('ranking optional arguments')
        group3.add_argument('--name', metavar='NAME', type=str, default="VSM",
                            help='the type of ranking (default: %(default)s)')
        group3.add_argument('-p1', metavar='SCHEME', type=str, default="lnc",
                            help='document scheme (default: %(default)s)')
        group3.add_argument('-p2', metavar='SCHEME', type=str, default="ltc",
                            help='query scheme (default: %(default)s)')
        group3.add_argument('-k1', metavar='N', type=float, default=1.2,
                            help='term frequency scaling (default: %(default)s)')
        group3.add_argument('-b', metavar='N', type=float, default=1,
                            help='document length normalization (default: %(default)s)')

        if args.help == 'indexer':
            parser.print_help()
            exit(0)

        args = parser.parse_args()
        init_indexer(args)


"""
TODO:
    ver tempos das queries e tal
    readme
"""
