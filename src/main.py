from tokenizer import Tokenizer
from indexer import Indexer

if __name__ == "__main__":
    tokenizer = Tokenizer(use_stopwords=False, use_stemmer=False)
    indexer = Indexer()

    with open("../dataset", "r") as f:
        f.readline()
        while f:
            terms, doc = tokenizer.tokenize(f.readline())
            indexer.index_terms(terms, doc)
