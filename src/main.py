import logging
from tokenizer import Tokenizer
from indexer import Indexer
from query import Query
from timeit import default_timer as timer

logging.basicConfig(level=logging.DEBUG,
                    format='\33[1m\33[34m%(filename)s:%(lineno)d %(asctime)s\33[0m - %(message)s', datefmt='%H:%M:%S')

if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords=False, stemmer=False)
    indexer = Indexer(file_location=True, file_location_step=3, doc_rename=True,
                      positional=True, tokenizer=tokenizer, load_zip=False, save_zip=False)

    start = timer()
    # indexer.index_file("../dataset")
    logging.info(f"Finished indexing ({timer() - start:.2f} seconds)")

    indexer.read_term_size_memory()
    query = Query(indexer)

    search = input("Search: ")

    start = timer()
    results = query.search(search)

    if results:
        logging.info(f"{len(results)} results ({timer() - start:.2f} seconds) ")
    else:
        logging.info(f"Your search - {search} - did not match any documents")


"""

index para os ficheiros gerados, com steps e usar binary search

"""
