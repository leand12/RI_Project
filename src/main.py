from tokenizer import Tokenizer
from indexer import Indexer

if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords=False, stemmer=False)
    indexer = Indexer(tokenizer=tokenizer, load_zip=False, save_zip=False)

    indexer.index_file("../dataset")

"""
positionals
index para os ficheiros gerados, com steps e usar binary search
rename dos ids para inteiros com um contador
ler ficheiros zipped
guardar index em zip

term #postings file_location
doc id
"""