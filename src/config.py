import json
from indexer import Indexer
from tokenizer import Tokenizer


def create_default_file(filename="config.json"):

    with open(filename, "w") as f:

        indexer = {
            "positional": False,
            "load_zip": False,
            "save_zip": False,
            "doc_rename": False,
            "file_location": False,
            "file_location_step": 100,
            "block_threshold": 1000000,
            "merge_file_size_threshold": 5000,
            "merge_chunk_size": 1000,
            "block_directory":"./block/",
            "merge_directory": "./indexer/",
            "term_info_filename": ".term_info"
        }

        tokenizer = {
            "min_length":3,
            "case_folding":True,
            "no_numbers":True,
            "stopwords":True,
            "contractions":True,
            "stemmer":True
        }

        data = {"indexer": indexer, "tokenizer": tokenizer}
        j = json.dump(data, f, indent=2)


def read_config(filename):
    with open(filename, "r") as f:
        data = json.loads(f.read())
    
    indexer_data = data.get("indexer")
    tokenizer_data = data.get("tokenizer")

    if tokenizer_data:
        tokenizer = Tokenizer(**tokenizer_data)
    else:
        tokenizer = Tokenizer()

    if indexer_data:
        indexer = Indexer(tokenizer=tokenizer, **indexer_data)
    else:
        indexer = Indexer(tokenizer=tokenizer)

    print(indexer_data)
    print(tokenizer_data)

create_default_file()
read_config("config.json")

