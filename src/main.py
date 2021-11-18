import logging
import argparse
from tokenizer import Tokenizer
from indexer import Indexer
from query import Query
from timeit import default_timer as timer


logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S',
                    format='\33[1m\33[34m%(filename)s:%(lineno)d %(asctime)s\33[0m - %(message)s')


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


parser = argparse.ArgumentParser(
    usage="main.py dataset [OPTIONS ...]",
    description='Document indexer using the SPIMI approach')
parser.add_argument('dataset', type=argparse.FileType('r'),
                    help='file with the documents to index')

indexer_parser = parser.add_argument_group('indexer optional arguments')
indexer_parser.add_argument('--positional', action='store_true',
                            help='save the terms\' positions in a document')
indexer_parser.add_argument('--load-zip', action='store_true',
                            help='')
indexer_parser.add_argument('--save-zip', action='store_true',
                            help='')
indexer_parser.add_argument('--doc-rename', action='store_true',
                            help='')
indexer_parser.add_argument('--file-location', action='store_true',
                            help='')
indexer_parser.add_argument('--file-location-step', metavar='STEP', type=int, default=100,
                            help='')
indexer_parser.add_argument('--block-threshold', metavar='THRESHOLD', type=int, default=1000000,
                            help='')
indexer_parser.add_argument('--merge-threshold', metavar='THRESHOLD', type=int, default=5000,
                            help='')
indexer_parser.add_argument('--merge-chunk-size', metavar='SIZE', type=int, default=1000,
                            help='')
indexer_parser.add_argument('--block-dir', metavar='DIR', type=dir_path, default="block/",
                            help='')
indexer_parser.add_argument('--merge-dir', metavar='DIR', type=dir_path, default="indexer/",
                            help='')

tokenizer_parser = parser.add_argument_group('tokenizer optional arguments')
tokenizer_parser.add_argument('--case-folding', action='store_true',
                              help='')
tokenizer_parser.add_argument('--no-numbers', action='store_true',
                              help='')
tokenizer_parser.add_argument('--stemmer', action='store_true',
                              help='')
tokenizer_parser.add_argument('--min-length', metavar='LENGTH', type=int, default=3,
                              help='')
tokenizer_parser.add_argument('--stopwords-file', metavar='FILE', type=argparse.FileType('r'), default="block/",
                              help='')
tokenizer_parser.add_argument('--contractions-file', metavar='FILE', type=argparse.FileType('r'), default="block/",
                              help='')

args = parser.parse_args()


if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords_file=None, stemmer=False)
    indexer = Indexer(file_location=True, file_location_step=3, rename_doc=True,
                      positional=True, tokenizer=tokenizer, load_zip=False, save_zip=False)

    start = timer()
    indexer.index_file("../dataset")
    logging.info(f"Finished indexing ({timer() - start:.2f} seconds)")

    indexer.read_term_size_memory()
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
