from tokenizer import Tokenizer
from indexer import Indexer

if __name__ == "__main__":
    tokenizer = Tokenizer(stopwords=False, stemmer=False)
    indexer = Indexer(tokenizer=tokenizer)

    indexer.index_file("../dataset")

"""

index para os ficheiros gerados
rename dos ids para inteiros com um contador



"""