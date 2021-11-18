import logging
import json
import math
import re
import sys
import os
import glob
import gzip
from tokenizer import Tokenizer
from utils import convert_size, get_directory_size


class Indexer:

    def __init__(self, tokenizer=Tokenizer(), positional=False, save_zip=False, rename_doc=False,
                 file_location=False, file_location_step=100,
                 block_threshold=1_000_000, merge_threshold=1_000_000, merge_chunk_size=1000,
                 block_dir="block/", merge_dir="indexer/", **ignore):

        self.positional = positional
        self.index = {}
        self.term_info = {}     # keeps the number of postings of a term
        path, _ = os.path.split(os.path.abspath(__file__))
        self.block_dir = path + "/" + block_dir
        self.merge_dir = path + "/" + merge_dir

        self.__block_cnt = 0
        # TODO: change this value or let it be set by the user
        self.block_threshold = block_threshold
        self.merge_threshold = merge_threshold
        self.merge_chunk_size = merge_chunk_size

        self.tokenizer = tokenizer

        self.save_zip = save_zip

        self.__doc_id_cnt = 0
        self.doc_ids = {}
        self.rename_doc = rename_doc

        self.file_location = file_location
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

    def write_block_disk(self):

        if not os.path.exists(self.block_dir):
            os.mkdir(self.block_dir)
        self.__post_cnt = 0
        # writes the current indexer block to disk
        with open(self.block_dir + "block" + str(self.__block_cnt) + ".txt", "w+") as f:
            self.__block_cnt += 1
            if self.positional:
                for term in sorted(self.index):
                    f.write(term + " " + " ".join([
                        doc + "," + ",".join(self.index[term][doc]) for doc in self.index[term]
                    ]) + "\n")
                    self.term_info.setdefault(term, [0, ''])[
                        0] += len(self.index[term])
            else:
                for term in sorted(self.index):
                    f.write(term + " " + " ".join(self.index[term]) + "\n")
                    self.term_info.setdefault(term, [0, ''])[
                        0] += len(self.index[term])
            self.index = {}

    def write_indexer_config(self):
        logging.info("Writing indexer config to disk")
        with open(self.merge_dir + ".metadata/config.json", "w") as f:

            indexer = {
                "positional": self.positional,
                "save_zip": self.save_zip,
                "rename_doc": self.rename_doc,
                "file_location": self.file_location,
                "file_location_step": self.file_location_step,
                "block_threshold": self.block_threshold,
                "merge_threshold": self.merge_threshold,
                "merge_chunk_size": self.merge_chunk_size,
                "block_dir": self.block_dir,
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
            j = json.dump(data, f, indent=2)

    def write_term_info_disk(self):
        logging.info("Writing # of postings for each term to disk")
        with open(self.merge_dir + ".metadata/term_info.txt", "w+") as f:
            for term in sorted(self.term_info):
                f.write(term + " " + " ".join(str(i)
                        for i in self.term_info[term]).strip() + "\n")

    def read_term_info_memory(self):
        logging.info("Reading # of postings for each term to memory")
        self.term_info = {}

        with open(self.merge_dir + ".metadata/term_info.txt", "r") as f:
            for line in f:
                term, *rest = line.strip().split(" ")
                self.term_info[term] = [int(i) for i in rest]

    def write_doc_ids(self):

        if not self.rename_doc:
            logging.warning(
                "Doc rename is not in use. Cannot write doc ids to disk.")
            return

        # TODO: allow user to choose the file where it is going to be stored???
        with open(self.merge_dir + ".metadata/doc_ids.txt", "w") as f:
            for doc_id, doc in self.doc_ids.items():
                f.write(doc_id + " " + doc + "\n")

    def read_doc_ids(self):

        if not self.rename_doc:
            logging.warning(
                "Doc rename is not in use. Cannot write doc ids to disk.")
            return

        self.doc_ids = {}
        with open(self.merge_dir + ".metadata/doc_ids.txt", "r") as f:
            for line in f:
                doc_id, doc = line.strip().split(" ")
                self.doc_ids[doc_id] = doc
        self.__doc_id_cnt = len(self.doc_ids)

    def read_posting_lists(self, term):

        # search for file
        files = glob.glob(self.merge_dir + "/*.txt")
        term_file = None
        for f in files:
            f_terms = f.split("/")[-1].split(".txt")[0].split(" ")
            if term >= f_terms[0] and term <= f_terms[1]:
                term_file = f
                break

        # search position on file
        if term_file != None:

            if self.file_location:
                term_location = 0
                sorted_term_info = sorted(self.term_info.keys())
                initial_term, final_term = term_file.split(
                    "/")[-1].split(".txt")[0].split(" ")

                # TODO: future work: binary search #
                for j, v in enumerate(sorted_term_info):
                    if v == initial_term:
                        break

                for i in range(j, len(sorted_term_info), self.file_location_step):
                    if sorted_term_info[i] <= term and sorted_term_info[i + self.file_location_step] > term:
                        term_location = i - j
                        break
                ##

                with open(term_file, "r") as f:
                    for i in range(term_location):
                        f.readline()

                    while True:
                        if self.positional:
                            term_r, *postings = f.readline().strip().split(" ")
                            postings = [pos.split(',')[0] for pos in postings]
                        else:
                            term_r, *postings = f.readline().strip().split(" ")

                        if term == term_r:
                            return postings
            else:
                with open(term_file, "r") as f:
                    for line in f:
                        if self.positional:
                            term_r, *postings = f.readline().strip().split(" ")
                            postings = [pos.split(',')[0] for pos in postings]
                        else:
                            term_r, *postings = line.strip().split(" ")

                        print(term_r, term)
                        if term_r == term:
                            return postings
        else:
            logging.error(
                "An error occured when searching for the term:" + term)
            exit(1)

    def clear_blocks(self):
        logging.info("Removing unused blocks")
        blocks = glob.glob(self.block_dir + "block*.txt")

        for block in blocks:
            try:
                os.remove(block)
            except:
                logging.error("Error removing block files")

        os.rmdir(self.block_dir)

    def open_file_to_index(self, filename):

        if filename.endswith(".gz"):
            try:
                f = gzip.open(filename, "rt")
            except gzip.BadGzipFile:
                logging.error(
                    "The provided file is not compatible with gzip format")
                exit(1)
        else:
            try:
                f = open(filename, "r")
            except:
                logging.error("Could not open the provided file")
                exit(1)
        return f

    def open_merge_file(self, filename):

        if self.save_zip:
            f = gzip.open(filename + ".gz", "wt")
        else:
            f = open(filename, "w")
        return f

    def merge_block_disk(self):

        if not os.path.exists(self.merge_dir):
            os.mkdir(self.merge_dir)
            os.mkdir(self.merge_dir + ".metadata/")

        # opens every block file and stores the file pointers in a list
        blocks = [open(block, "r")
                  for block in glob.glob(self.block_dir + "*")]
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
                        line = doc.strip().split(" ")
                        term, doc_lst = line[0], line[1:]
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
                with self.open_merge_file(self.merge_dir + sorted_terms[0] + " " + term + ".txt") as f:
                    for ti, t in enumerate(sorted_terms):
                        if t <= term:
                            f.write(
                                t + " " + " ".join(sorted(terms[t])) + "\n")
                            if self.file_location and ti % self.file_location_step == 0:
                                self.term_info[t][1] = ti + 1
                            del terms[t]
            elif not blocks:
                # this will write the terms left in the last block
                with self.open_merge_file(self.merge_dir + sorted_terms[0] + " " + term + ".txt") as f:
                    for ti, t in enumerate(sorted_terms):
                        f.write(t + " " + " ".join(sorted(terms[t])) + "\n")
                        if self.file_location and ti % self.file_location_step == 0:
                            self.term_info[t][1] = ti + 1
                        del terms[t]

        self.clear_blocks()

    def index_terms(self, terms, doc):
        # indexes a list of terms provided by the tokenizer

        if self.rename_doc:
            doc_id = str(self.__doc_id_cnt)
            self.doc_ids[doc_id] = doc
            doc = doc_id
            self.__doc_id_cnt += 1

        # the last indexes need to be written to a block is not full
        if self.__post_cnt >= self.block_threshold:
            logging.info("Writing to disk")
            self.write_block_disk()

        # terms -> List[Tuple(term, pos)]
        for term, pos in terms:
            if self.positional:
                # index -> Dict[term: Dict[doc: List[pos]]]
                self.index.setdefault(term, {doc: []}) \
                    .setdefault(doc, []) \
                    .append(pos)
            else:
                # index -> Dict[term: List[doc]]
                self.index.setdefault(term, [])
                self.index[term].append(doc)
        self.__post_cnt += len(terms)

    def index_file(self, filename, skip_lines=1):

        with self.open_file_to_index(filename) as f:
            for _ in range(skip_lines):
                f.readline()
            while f:
                line = f.readline()

                if len(line) == 0:
                    self.write_block_disk()
                    break
                terms, doc = self.tokenizer.tokenize(line)
                self.index_terms(terms, doc)

            self.merge_block_disk()
            self.write_term_info_disk()
            if self.rename_doc:
                self.write_doc_ids()
            self.write_indexer_config()
