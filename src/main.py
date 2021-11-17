from tokenizer import Tokenizer
from indexer import Indexer
from query import Query

if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords=False, stemmer=False)
    indexer = Indexer(file_location=True, file_location_step=3, doc_rename=True, positional=True, tokenizer=tokenizer, load_zip=False, save_zip=False)

    indexer.index_file("../dataset")
    indexer.read_term_size_memory()
    query = Query(indexer)

    q = input("Search: ")
    query.search(q)


"""

index para os ficheiros gerados, com steps e usar binary search

"""
