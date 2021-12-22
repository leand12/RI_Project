# Bruno Bastos 93302
# Leandro Silva 93446

import logging
import time
import json
import math
import re
import sys
import os
import glob
import gzip
from tokenizer import Tokenizer
from utils import convert_size, get_directory_size
from query import BM25, VSM


class TermInfo():

    def __init__(self, posting_size=0, position=None, idf=None):
        self.posting_size = posting_size
        self.position = position or None
        self.idf = idf or None

    def __str__(self):
        return f"{self.posting_size},{self.position or ''},{self.idf or ''}"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def create(line):
        term, posting_size, position, idf = line.strip().split(',')
        return TermInfo(int(posting_size), 
            position and int(position), idf and float(idf))
    

class Indexer:

    def __init__(self, tokenizer=Tokenizer(), positional=False, save_zip=False, rename_doc=False, file_location_step=0,
                 block_threshold=1_000_000, merge_threshold=1_000_000, merge_chunk_size=1000,
                 ranking=None, merge_dir="indexer/", **ignore):

        self.positional = positional
        self.index = {}             # {term: {doc: [pos]}} || {term: [docs]}
        self.term_info = {}         # {term: [df, file_loc]}

        path, _ = os.path.split(os.path.abspath(__file__))
        self.merge_dir = merge_dir if os.path.isabs(
            merge_dir) else path + "/" + merge_dir

        self.__block_cnt = 0
        self.block_threshold = block_threshold
        self.merge_threshold = merge_threshold
        self.merge_chunk_size = merge_chunk_size

        self.tokenizer = tokenizer

        self.save_zip = save_zip

        self.ranking = ranking         # ranking object

        # VS
        self.n_doc_indexed = 0
        self.term_doc_weights = {}

        # BM25
        self.document_lens = {}     # saves the number of words for each document
        self.term_frequency = {}    # save

        # RENAME DOC
        self.__last_rename = 0
        self.doc_ids = {}
        self.rename_doc = rename_doc

        # FILE LOCATION
        self.file_location_step = file_location_step
        self.__post_cnt = 0

    @property
    def vocabulary_size(self):
        return len(self.term_info)

    @property
    def num_segments(self):
        return self.__block_cnt

    @property
    def disk_size(self):
        return convert_size(get_directory_size(self.merge_dir))

    @staticmethod
    def load_metadata(directory):
        """Static method that creates an Indexer object from a directory using the metadata."""

        indexer = Indexer.read_config(directory + ".metadata/config.json")
        indexer.read_term_info_memory()
        if indexer.rename_doc:
            indexer.read_doc_ids()

        return indexer

    @staticmethod
    def read_config(filename):
        """Static method that creates an Indexer object by providing a config file."""

        with open(filename, "r") as f:
            data = json.loads(f.read())

            indexer_data = data.get("indexer", {})
            tokenizer_data = data.get("tokenizer", {})
            ranking_data = data.get("ranking", {})

            ranking = None
            if ranking_data.get("name") == "BM25":
                ranking = BM25(**ranking_data)
            elif ranking_data.get("name") == "VSM":
                ranking = VSM(**ranking_data)

            tokenizer = Tokenizer(**tokenizer_data)
            indexer = Indexer(
                ranking=ranking, tokenizer=tokenizer, **indexer_data)

            return indexer

    @staticmethod
    def create_default_file(filename="config.json"):
        """Static method that creates a configuration file with the default configurations."""

        with open(filename, "w") as f:
            indexer = {
                "positional": False,
                "save_zip": False,
                "rename_doc": False,
                "file_location_step": 0,
                "block_threshold": 1_000_000,
                "merge_threshold": 1_000_000,
                "merge_chunk_size": 1000,
                "merge_dir": "indexer/",
            }
            tokenizer = {
                "min_length": 3,
                "case_folding": True,
                "no_numbers": True,
                "stopwords_file": None,
                "contractions_file": None,
                "stemmer": True
            }
            ranking = {
                "name": "VS",
                "p1": "lnc",
                "p2": "ltc"
            }

            data = {"ranking": ranking,
                    "indexer": indexer, "tokenizer": tokenizer}
            json.dump(data, f, indent=2)

    def write_block_disk(self):
        """Writes the current block to disk."""

        logging.info("Writing block to disk")
        block_dir = self.merge_dir + "block/"
        if not os.path.exists(self.merge_dir):
            os.mkdir(self.merge_dir)
        if not os.path.exists(block_dir):
            os.mkdir(block_dir)

        # resets the number of postings in memory
        self.__post_cnt = 0

        with open(f"{block_dir}block{self.__block_cnt}.txt", "w+") as f:
            self.__block_cnt += 1

            for term in sorted(self.index):
                if self.positional:
                    # term doc1,pos1,pos2 doc2,pos1
                    write = f"{term} {' '.join([doc + ',' + ','.join(self.index[term][doc]) for doc in self.index[term]])}\n"
                else:
                    # term doc1 doc2
                    write = f"{term} {' '.join(self.index[term])}\n"

                f.write(write)
                self.term_info.setdefault(
                    term, TermInfo()).posting_size += len(self.index[term])

            self.index = {}

    def write_indexer_config(self):
        """Saves the current configuration as metadata."""

        logging.info("Writing indexer config to disk")
        with open(f"{self.merge_dir}.metadata/config.json", "w") as f:

            indexer = {
                "positional": self.positional,
                "save_zip": self.save_zip,
                "rename_doc": self.rename_doc,
                "file_location_step": self.file_location_step,
                "block_threshold": self.block_threshold,
                "merge_threshold": self.merge_threshold,
                "merge_chunk_size": self.merge_chunk_size,
                "merge_dir": self.merge_dir,
            }
            tokenizer = {
                "min_length": self.tokenizer.min_length,
                "case_folding": self.tokenizer.case_folding,
                "no_numbers": self.tokenizer.no_numbers,
                "stopwords_file": self.tokenizer.stopwords_file,
                "contractions_file": self.tokenizer.contractions_file,
                "stemmer": True if self.tokenizer.stemmer else False
            }
            data = {"indexer": indexer, "tokenizer": tokenizer}

            if self.ranking:
                data["ranking"] = self.ranking.__dict__

            json.dump(data, f, indent=2)

    def write_term_info_disk(self):
        """Saves term information as metadata."""

        logging.info("Writing # of postings for each term to disk")
        with open(self.merge_dir + ".metadata/term_info.txt", "w+") as f:

            # term posting_size file_location_step
            # FIXME: se tivessemos o term info como objeto era mais facil de escrever em ficheiros XD
            for term in sorted(self.term_info):
                f.write(f"{term},{self.term_info[term]}\n")

    def read_term_info_memory(self):
        """Reads term information from metadata."""

        logging.info("Reading term info to memory")
        self.term_info = {}

        with open(f"{self.merge_dir}.metadata/term_info.txt", "r") as f:
            for line in f:
                term, _ = line.strip().split(',', 1)
                self.term_info[term] = TermInfo.create(line)

    def write_doc_ids(self):
        """Saves the dict containing the new ids for the documents as metadata."""

        if not self.rename_doc:
            logging.warning(
                "Doc rename is not in use. Cannot write doc ids to disk.")
            return

        with open(f"{self.merge_dir}.metadata/doc_ids.txt", "w") as f:
            for doc_id, doc in self.doc_ids.items():
                f.write(f"{doc_id} {doc}\n")

    def read_doc_ids(self):
        """Reads document id conversion from metadata."""

        if not self.rename_doc:
            logging.warning(
                "Doc rename is not in use. Cannot write doc ids to disk.")
            return

        self.doc_ids = {}
        with open(f"{self.merge_dir}.metadata/doc_ids.txt", "r") as f:
            for line in f:
                doc_id, doc = line.strip().split(" ")
                self.doc_ids[doc_id] = doc
        # FIXME: maybe set the __last_rename when reading from disk
    def __get_filename(self, path):
        return path.split("/")[-1].replace(".gz", "").split(".txt")[0]

    def __get_term_location(self, term):

        if self.file_location_step == 1:
            return self.term_info[term].position
        
        sorted_term_info = sorted(self.term_info.keys())

        low = index = 0
        high = len(sorted_term_info) - 1

        while low <= high:
            index = (high + low) // 2
            if sorted_term_info[index] < term:
                low = index + 1
            elif sorted_term_info[index] > term:
                high = index - 1
            else:
                break

        for i in range(self.file_location_step):
            pos = self.term_info[sorted_term_info[index-i]].position
            if pos:
                # previous term has file location
                return pos + i

    def __get_term_info_from_file(self, term, file, skip=0):

        with self.open_merge_file(file.replace(".gz", ""), "r") as f:
            for _ in range(skip):
                f.readline()

            while (line := f.readline()):

                if self.positional:
                    # TODO: positions are not being used
                    term_r, *postings = line.strip().split(" ")
                    postings = [pos.split(',')[:2] for pos in postings]
                else:
                    term_r, *postings = line.strip().split(" ")
                    postings = [pos.split(',') for pos in postings]

                if term == term_r:
                    weights = [pos[1] for pos in postings]
                    postings = [pos[0] for pos in postings]
                    return weights, postings

    def read_posting_lists(self, term):
        """Reads the posting list of a term from disk."""

        if not os.path.exists(self.merge_dir):
            logging.error(
                "Index Directory does not exist. Cannot read posting lists.")

        # search for file
        files = glob.glob(f"{self.merge_dir}/*.txt*")
        term_file = None
        for f in files:
            f_terms = self.__get_filename(f).split(" ")
            if f_terms[0] <= term <= f_terms[1]:
                term_file = f
                break

        # search position on file
        if term_file != None and term in self.term_info:
            # FIXME: what if no ranking
            
            idf = self.term_info[term].idf
            if self.file_location_step:
                term_location = self.__get_term_location(term)
                weights, postings = self.__get_term_info_from_file(term, term_file, term_location - 1)
            else:
                weights, postings = self.__get_term_info_from_file(term, term_file)
            return idf, weights, postings

        logging.error(
            f"An error occured when searching for the term: {term}")
        # FIXME: return None or exception?
        return None

    def clear_blocks(self):
        """Remove blocks folder."""

        logging.info("Removing unused blocks")
        block_dir = f"{self.merge_dir}block/"
        if not os.path.exists(block_dir):
            logging.error(
                "Block directory does not exist. Could not remove blocks.")
            exit(1)

        blocks = glob.glob(f"{block_dir}block*.txt")

        for block in blocks:
            try:
                os.remove(block)
            except:
                logging.error("Error removing block files")

        os.rmdir(block_dir)

    def open_file_to_index(self, filename):
        """Open and return the dataset file."""
        # FIXME: what
        try:
            f = open(filename, "r")
            f.readline()  # skip header
            return f
        except:
            pass

        try:
            f = gzip.open(filename, "rt")
            f.readline()  # skip header
            return f
        except gzip.BadGzipFile:
            pass

        logging.error("Could not open the provided file")
        exit(1)

    def open_merge_file(self, filename, mode="w"):
        """Open and return a index file."""
        if self.save_zip and not filename.endswith(".gz"):
            filename += ".gz"

        if filename.endswith(".gz"):
            return gzip.open(filename, mode + "t")
        return open(filename, mode)

    def merge_block_disk(self):
        """Merge all blocks in disk."""
        logging.info("Merge Block disk")
        if not os.path.exists(self.merge_dir):
            os.mkdir(self.merge_dir)
        if not os.path.exists(f"{self.merge_dir}.metadata/"):
            os.mkdir(f"{self.merge_dir}.metadata/")

        # opens every block file and stores the file pointers in a list
        blocks = [open(block, "r")
                  for block in glob.glob(f"{self.merge_dir}block/*")]
        terms = {}
        # keeps the last term for every block
        last_terms = [None for _ in range(len(blocks))]
        last_term = None                                    # keeps the min last term

        while blocks or terms:
            b = 0
            while b != len(blocks):
                # check if the last_term is the same as the last_term for the block
                if last_term == last_terms[b]:
                    f = blocks[b]
                    docs = f.readlines(self.merge_chunk_size)
                    # if the file ends it needs to be removed from the lists
                    if not docs:
                        f.close()
                        del blocks[b]
                        del last_terms[b]
                        continue

                    for doc in docs:
                        line = doc.strip().split(' ')
                        term, doc_lst = line[0], line[1:]
                        if self.ranking:
                            for i, doc_str in enumerate(doc_lst):
                                doc = doc_str.split(',', 1)[0]
                                # doc_lst[i] += ',' + self.term_doc_weights[term][doc]
                                n = len(doc)
                                # if term == '000o':
                                doc_lst[i] = f"{doc_str[:n]},{self.term_doc_weights[term][doc]}{doc_str[n:]}"
                        terms.setdefault(term, set()).update(doc_lst)
                    last_terms[b] = term
                b += 1

            # last_term is only updated if the list is not empty
            last_term = min(last_terms) if last_terms else last_term

            total = 0
            sorted_terms = sorted(terms)
            for term in sorted_terms:
                if term >= last_term:
                    break
                total += len(terms[term])
                if total >= self.merge_threshold:
                    break

            if total >= self.merge_threshold:
                # writes the terms to the file when the terms do not go pass a threshold
                self.__store_term_merged_file(terms, sorted_terms, term, True)
            elif not blocks:
                # this will write the terms left in the last block
                self.__store_term_merged_file(terms, sorted_terms, term)

        self.clear_blocks()

    def __store_term_merged_file(self, terms, sorted_terms, last_term, threshold_term=False):

        with self.open_merge_file(f"{self.merge_dir}{sorted_terms[0]} {last_term}.txt") as f:
            for ti, t in enumerate(sorted_terms):
                if not threshold_term or t <= last_term:
                    f.write(f"{t} {' '.join(sorted(terms[t]))}\n")
                    if self.file_location_step and ti % self.file_location_step == 0:
                        self.term_info[t].pos = ti + 1
                    del terms[t]

    def __next_doc_id(self):
        
        max_char = 126
        min_char = 33
        doc_id = list(self.__last_rename) or list(chr(min_char))
        # [33 126]
        i = -1
        while True:
            if ord(doc_id[i]) == max_char:
                doc_id[i] = chr(min_char)
                if i == -len(doc_id):
                    doc_id[:0] = [chr(min_char - 1)] 
            else:
                doc_id[i] = chr(ord(doc_id[i]) + 1)
                break
            i -= 1
        return "".join(doc_id)

    def __get_new_doc_id(self, doc):

        # FIXME: __doc_id_cnt is the same as n_doc_indexed
        doc_id = self.__next_doc_id()
        self.doc_ids[doc_id] = doc
        return doc_id

    def __calculate_ranking_info(self, terms, doc):
        if not self.ranking:
            return

        temp = [term for term, pos in terms]

        if self.ranking.name == "VSM": 
            cos_norm = 0

            for term in set(temp):
                self.term_doc_weights.setdefault(term, {})
                if self.ranking.p1[0] == "l":
                    # l**
                    self.term_doc_weights[term][doc] = 1 + math.log10(temp.count(term))
                elif self.ranking.p1[0] == "n":
                    # n**
                    self.term_doc_weights[term][doc] = temp.count(term)
                
                cos_norm += self.term_doc_weights[term][doc]**2
            
            if self.ranking.p1[2] == "c":
                # **c
                cos_norm = 1 / math.sqrt(cos_norm)
                for term in set(temp):
                    self.term_doc_weights[term][doc] *= cos_norm

        elif self.ranking.name == "BM25":
            self.document_lens[doc] = len(terms)
            
            for term in set(temp):
                self.term_frequency.setdefault(term, {})
                self.term_frequency[term][doc] = temp.count(term)

    def index_terms(self, terms, doc):
        """
        Index a list of terms provided by the tokenizer.

        @param terms: the list of terms
        @param doc: the document ID
        """
        # indexes a list of terms provided by the tokenizer

        if self.rename_doc:
            doc = self.__get_new_doc_id(doc)

        self.__calculate_ranking_info(terms, doc)

        # terms -> List[Tuple(term, pos)]
        for term, pos in terms:
            if self.positional:
                # index -> Dict[term: Dict[doc: List[pos]]]
                self.index.setdefault(term, {doc: []}) \
                    .setdefault(doc, []) \
                    .append(pos)
            else:
                # index -> Dict[term: List[doc]]
                self.index.setdefault(term, set()) \
                    .add(doc)
        self.__post_cnt += len(terms)

    def index_file(self, filename):
        """
        Create the indexer for a dataset.

        @param filename: the dataset filename
        """
        with self.open_file_to_index(filename) as f:
            while f:
                line = f.readline()

                # writes block to disk when there are more postings than the threshold
                # or when the file ends
                if not line or self.__post_cnt >= self.block_threshold:
                    self.write_block_disk()
                if not line:
                    break

                terms, doc = self.tokenizer.tokenize(line)

                if not terms:
                    continue

                self.index_terms(terms, doc)
                self.n_doc_indexed += 1

        if self.ranking:
            self.__calculate_idf()
            if self.ranking.name == "BM25":
                self.__calculate_ci()

        self.merge_block_disk()
        self.write_term_info_disk()
        if self.rename_doc:
            self.write_doc_ids()
        self.write_indexer_config()

    def __calculate_idf(self):

        for term in self.term_info:
            document_frequency = self.term_info[term].posting_size
            idf = math.log10(self.n_doc_indexed / document_frequency)
            self.term_info[term].idf = idf

    def __calculate_ci(self):

        self.term_doc_weights = {}     # {term : {doc: ci}}
        avdl = sum(self.document_lens.values()) / \
            len(self.document_lens)  # TODO: this is slow

        for term in self.term_frequency:
            idf = self.term_info[term].idf

            for doc in self.term_frequency[term]:
                term_frequency = self.term_frequency[term][doc]
                document_len = self.document_lens[doc]

                ci = idf * (self.ranking.k1 + 1) * term_frequency / (self.ranking.k1 *
                    ((1 - self.ranking.b) + self.ranking.b * document_len/avdl) + term_frequency)
                self.term_doc_weights.setdefault(term, {})
                self.term_doc_weights[term][doc] = ci
