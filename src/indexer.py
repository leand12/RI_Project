import re
import sys


class Indexer:

    def __init__(self, save_positions=False, directory=""):
        self.save_positions = save_positions
        self.index = {}
        self.term_posting_size = {}     # keeps the number of postings of a term
        self.dir = directory
        self.block_cnt = 0
        self.threshold = 10000         # change this value or let it be set by the user
        self.block_threshold = 3

    def write_block_disk(self):
        # writes the current indexer block to disk
        with open(self.dir + "block" + str(self.block_cnt) + ".txt", "w+") as f:
            self.block_cnt += 1
            if self.save_positions:
                assert False, "Not implemented"
            else:
                
                for term in sorted(self.index.keys()):
                    for posting in self.index[term]:
                        f.write(term + " " + str(posting) + "\n")

                self.term_posting_size[term] = len(self.index[term])
                self.index = {}

        if self.block_cnt == self.block_threshold:
            self.merge_block_disk()
            self.block_cnt = 0

    def read_term_to_memory(self, term):
        # TODO: we need to know where this term is stored
        # maybe use an index that points to a certain letter and start read from there
        with open("random.txt", "r") as f:
           pass


    def merge_block_disk(self):
        # TODO: mapReduce should be used here somewhere
        # merges the block files in disk
        print("Merging blocks")
        pass

    def index_terms(self, terms, doc):
        # indexes a list of terms provided by the tokenizer
    
        if len(self.index.values()) >= self.threshold:
            print("Writing to disk")
            self.write_block_disk()

        # terms -> List[Tuple(term, pos)]
        # FIXME: need the positions but tokenizer is not ready yet
        #for term, pos in terms:
        for term in terms:
            if self.save_positions:
                # index -> Dict[term: Dict[doc: List[pos]]]
                self.index.setdefault(term, {doc: []}) \
                    .setdefault(doc, []) \
                    .append(pos)
            else:
                # index -> Dict[term: List[doc]]
                self.index.setdefault(term, [])
                self.index[term].append(doc)
