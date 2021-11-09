from tokenizer import Tokenizer
from indexer import Indexer

if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords=False, stemmer=False)
    indexer = Indexer()

    with open("../dataset", "r") as f:
        f.readline()
        while f:
            line = f.readline()
            if not line:
                break
            terms, doc = tokenizer.tokenize(line)
            indexer.index_terms(terms, doc)

        indexer.merge_block_disk()
