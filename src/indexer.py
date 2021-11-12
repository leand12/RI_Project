import logging
import re
import sys
import os
import glob
import gzip
from tokenizer import Tokenizer

logging.basicConfig(level=logging.DEBUG, format='%(filename)s:%(lineno)d %(asctime)s - %(message)s', datefmt='%H:%M:%S')

class Indexer:

    def __init__(self, tokenizer=Tokenizer(), positional=False, load_zip=False, save_zip=False, doc_rename=False,
         block_threshold=50000, merge_file_size_threshold=5000, merge_chunk_size=1000,
         block_directory="./block/", merge_directory="./indexer/", term_sizes_filename="term_sizes"):
        
        self.positional = positional
        self.index = {}
        self.term_posting_size = {}     # keeps the number of postings of a term
        self.block_directory = block_directory
        self.merge_directory = merge_directory
        self.term_sizes_filename = term_sizes_filename    # FIXME: this does not work if the user provides a directory instead of a file
        self.block_cnt = 0
        self.block_threshold = block_threshold         # change this value or let it be set by the user
        self.merge_file_size_threshold = merge_file_size_threshold
        self.merge_chunk_size = merge_chunk_size
        self.tokenizer = tokenizer
        self.load_zip = load_zip
        self.save_zip = save_zip
        self.doc_id_cnt = 0
        self.doc_ids = {}
        self.doc_rename = doc_rename

    def write_block_disk(self):

        if not os.path.exists(self.block_directory):
            os.mkdir(self.block_directory)

        # writes the current indexer block to disk
        with open(self.block_directory + "block" + str(self.block_cnt) + ".txt", "w+") as f:
            self.block_cnt += 1
            if self.positional:
                assert False, "Not implemented"
            else:
                
                for term in sorted(self.index.keys()):
                    f.write(term + " " + " ".join(self.index[term]) + "\n")
                    self.term_posting_size.setdefault(term, 0)
                    self.term_posting_size[term] += len(self.index[term])
                self.index = {}

    def write_term_size_disk(self):
        logging.info("Writing # of postings for each term to disk")
        with open(self.merge_directory + self.term_sizes_filename + ".txt", "w+") as f:
            for term in self.term_posting_size:
                f.write(term + " " + str(self.term_posting_size[term]) + "\n")

    def read_term_size_memory(self):
        logging.info("Reading # of postings for each term to memory")
        self.term_posting_size = {}

        with open(self.merge_directory + self.term_sizes_filename + ".txt", "r") as f:
            for line in f:
                term, postings = line.strip().split(" ")
                self.term_posting_size[term] = int(postings)

    def write_doc_ids(self):

        if not self.doc_rename:
            logging.warning("Doc rename is not in use. Cannot write doc ids to disk.")
            return

        # TODO: allow user to choose the file where it is going to be stored???
        with open(self.merge_directory + "doc_ids" + ".txt", "w") as f:
            for doc_id, doc in self.doc_ids.items():
                f.write(doc_id + " " + doc + "\n")

    def read_doc_ids(self):

        if not self.doc_rename:
            logging.warning("Doc rename is not in use. Cannot write doc ids to disk.")
            return

        self.doc_ids = {}
        with open(self.merge_directory + "doc_ids" + ".txt", "r") as f:
            for line in f:
                doc_id, doc = line.strip().split(" ")
                self.doc_ids[doc_id] = doc
        self.doc_id_cnt = len(self.doc_ids)

    def clear_blocks(self):
        logging.info("Removing unused blocks")
        blocks = glob.glob("./block/block*.txt")
        
        for block in blocks:
            try:
                os.remove(block)
            except:
                logging.error("Error removing block files")
        
        os.rmdir(self.block_directory)

    def merge_block_disk(self):
    
        if not os.path.exists(self.merge_directory):
            os.mkdir(self.merge_directory)

        # opens every block file and stores the file pointers in a list
        blocks = [open(block, "r") for block in glob.glob(self.block_directory + "*")]
        terms = {}
        last_terms = [None for _ in range(len(blocks))]     # keeps the last term for every block
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
            sorted_terms = sorted(terms.keys())
            for term in sorted_terms:
                if term >= last_term:
                    break
                total += len(terms[term])
                if total >= self.merge_file_size_threshold:
                    break

            if total >= self.merge_file_size_threshold:
                # writes the terms to the file when the terms do not go pass a threshold
                with self.open_merge_file(self.merge_directory + sorted_terms[0] + "-" + last_term + ".txt") as f:
                    for t in sorted_terms:
                        if t <= term:
                            f.write(t + " " + " ".join(sorted(terms[t])) + "\n")
                            del terms[t]
            elif not blocks:
                # this will write the terms left in the last block
                with self.open_merge_file(self.merge_directory + sorted_terms[0] + "-" + last_term + ".txt") as f:
                    for t in sorted_terms:
                        f.write(t + " " + " ".join(sorted(terms[t])) + "\n")
                        del terms[t]

        self.clear_blocks()

    def index_terms(self, terms, doc):
        # indexes a list of terms provided by the tokenizer
    
        if self.doc_rename:
            doc_id = str(self.doc_id_cnt)
            self.doc_ids[doc_id] = doc
            doc = doc_id
            self.doc_id_cnt += 1

        # the last indexes need to be written to a block is not full
        if len(self.index.values()) >= self.block_threshold:
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

    def index_file(self, filename, skip_lines=1):

        with self.get_file_to_index(filename) as f:
            for _ in range(skip_lines):
                f.readline()
            while f:
                line = f.readline()
                
                if len(line) == 0:
                    # FIXME: if the file ends and it does not reach the trehshold the last terms
                    # will not be written to disk in a block
                    # this fixes it but is bad
                    self.write_block_disk()
                    break
                terms, doc = self.tokenizer.tokenize(line)
                self.index_terms(terms, doc)

            self.merge_block_disk()
            self.write_term_size_disk()
            if self.doc_rename:
                self.write_doc_ids()

    def get_file_to_index(self, filename):

        if self.load_zip:
            try:
                f = gzip.open(filename, "rt")
            except gzip.BadGzipFile:
                logging.error("The provided file is not compatible with gzip format")
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

