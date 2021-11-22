# Bruno Bastos 93302
# Leandro Silva 93446

import os
import logging
import coloredlogs
import argparse
from tokenizer import Tokenizer
from indexer import Indexer
from query import Query
from timeit import default_timer as timer

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='DEBUG', logger=logger)
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

parser.add_argument('-c', '--config', metavar='FILE',
                    help='json file with the configurations to build the tokenizer and indexer')

group1 = parser.add_argument_group('indexer optional arguments')
group1.add_argument('--positional', action='store_true',
                    help='save the terms\' positions in a document')
group1.add_argument('--save-zip', action='store_true',
                    help='zip the output files of the indexer')
group1.add_argument('--doc-rename', action='store_true',
                    help='rename document IDs for a more efficient space usage')
group1.add_argument('--file-location', action='store_true',
                    help='')
group1.add_argument('--file-location-step', metavar='STEP', type=int, default=100,
                    help='')
group1.add_argument('--block-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                    help='maximum number of documents that can be stored in a block (default: %(default)s)')
group1.add_argument('--merge-threshold', metavar='THRESHOLD', type=int, default=1_000_000,
                    help='maximum number of documents that can be stored in a index (default: %(default)s)')
group1.add_argument('--merge-chunk-size', metavar='SIZE', type=int, default=1000,
                    help='size of the block chunks read (default: %(default)s)')
group1.add_argument('--block-dir', metavar='DIR', default="block/",
                    help='source directory path to store the blocks (default: %(default)s)')
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

args = vars(parser.parse_args())

if __name__ == "__main__":
    if args["dataset"]:
        if args["config"]:
            indexer = Indexer.read_config(args["config"])
        else:
            tokenizer = Tokenizer(**args)
            indexer = Indexer(tokenizer=tokenizer, **args)

        start = timer()
        indexer.index_file(args["dataset"])
        logging.info(f"Finished indexing ({timer() - start:.2f} seconds)")
        logging.info(f"Vocabulary size: {indexer.vocabulary_size}")
        logging.info(f"Index size on disk: {indexer.disk_size}")
        logging.info(f"Index segments written to disk: {indexer.num_segments}")

    start = timer()
    indexer = Indexer.load_metadata(args["indexer"] if args["indexer"] else indexer.merge_dir)
    logging.info(
        f"Time taken to start up index: {timer() - start:.2f} seconds")

    query = Query(indexer)

    search = input("Search: ")

    start = timer()
    results = query.search(search)

    if results:
        logging.info(
            f"{len(results)} results ({timer() - start:.2f} seconds)")
    else:
        logging.info(f"Your search - {search} - did not match any documents")
