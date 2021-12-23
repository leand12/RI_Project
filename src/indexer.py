# Bruno Bastos 93302
# Leandro Silva 93446

import logging
import json
import math
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

    @staticmethod
    def create(line):
        term, idf, position = line.strip().split(',')
        return TermInfo(0, position and int(position), idf and float(idf))

    def write(self):
        # TODO: BM25 remove idf and fix this error
        return f"{self.idf or '':.6f},{self.position or ''}"


class PostingInfo():
    def __init__(self, doc_id, term_freq, positions, weight=None):
        self.doc_id = doc_id
        self.positions = positions
        self.weight = weight
        self.term_freq = term_freq

    @staticmethod
    def create(line, positional=False):
        if not positional:
            pos = None
            d, w, tf = line.strip().split(',', 2)
        else:
            d, w, tf, pos = line.strip().split(',', 3)
        return PostingInfo(d, tf and int(tf), pos, w and float(w))

    def write_to_block(self):
        # doc,w,tf,pos
        w = p = ''
        if self.weight:
            w = f"{self.weight:.6f}"
        if self.positions:
            p = ',' + self.positions
        return f"{self.doc_id},{w},{self.term_freq or ''}{p}"

    def write_to_index(self):
        # doc,w,pos
        w = p = ''
        if self.weight:
            w = f"{self.weight:.6f}"
        if self.positions:
            p = ',' + self.positions
        return f"{self.doc_id},{w}{p}"


class Indexer:

    def __init__(self, tokenizer=Tokenizer(), positional=False, save_zip=False, rename_doc=False, file_location_step=0,
                 block_threshold=1_000_000, merge_threshold=1_000_000, merge_chunk_size=1000,
                 ranking=VSM(), merge_dir="indexer/", **ignore):

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

        self.ranking = ranking

        # VSM
        self.__n_doc_indexed = 0
        self.term_doc_weights = {}   # term_doc_weights keeps the information for either bm25 o

        # BM25
        self.document_lens = {}     # saves the number of words for each document
        self.term_frequency = {}    # save
        self.__total_doc_lens = 0

        # rename document ID
        self.__last_rename = ""
        self.doc_ids = {}
        self.rename_doc = rename_doc

        # file location
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

        logging.info(f"Writing block {self.__block_cnt} to disk")
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
                f.write(term)
                # term doc1,w,tf,pos1,pos2 doc2,pos1
                for doc in self.index[term]:
                    weight = positions = None

                    if self.ranking.name == 'VSM':
                        weight = self.term_doc_weights[term][doc]
                    if self.positional:
                        positions = self.index[term][doc]

                    tf = self.term_frequency[term][doc]
                    f.write(" " + PostingInfo(doc, tf,
                                              positions, weight).write_to_block())
                f.write("\n")
                self.term_info.setdefault(
                    term, TermInfo()).posting_size += len(self.index[term])

        self.index.clear()
        self.term_doc_weights.clear()
        self.term_frequency.clear()

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

            # term idf file_location_step
            for term in sorted(self.term_info):
                f.write(f"{term},{self.term_info[term].write()}\n")

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

    def __get_filename(self, path):
        return path.split("/")[-1].replace(".gz", "").split(".txt")[0]

    def __get_term_location(self, term):
        """
        Get the location of a term on a file.
        If the file location step is provided, a binary search is performed.
        """
        if self.file_location_step == 1:
            return self.term_info[term].position

        # binary search
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

    def __get_term_postings_from_file(self, term, filename, skip=0):
        """Get the term postings and weights from a index file."""

        with self.open_merge_file(filename.replace(".gz", ""), "r") as f:
            for _ in range(skip):
                f.readline()

            while (line := f.readline()):

                term_r, *postings = line.strip().split(" ")

                if term == term_r:
                    if self.positional:
                        # TODO: positions are not being used
                        postings = [post.split(',')[:2] for post in postings]
                    else:
                        postings = [post.split(',') for post in postings]

                    weights = [post[1] for post in postings]
                    if self.rename_doc:
                        postings = [self.doc_ids[post[0]] for post in postings]
                    else:
                        postings = [post[0] for post in postings]
                    return weights, postings

    def read_posting_lists(self, term):
        """Reads the posting list of a term from disk."""

        if not os.path.exists(self.merge_dir):
            logging.error("Index Directory does not exist. Cannot read posting lists.")
            exit(1)

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
            idf = self.term_info[term].idf
            if self.file_location_step:
                term_location = self.__get_term_location(term)
                weights, postings = self.__get_term_postings_from_file(
                    term, term_file, term_location - 1)
            else:
                weights, postings = self.__get_term_postings_from_file(
                    term, term_file)
            return idf, weights, postings

        logging.warning(f"Ignoring term \"{term}\"")
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

        logging.info("Merging blocks from disk")
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

        curr = 0
        while blocks or terms:
            b = 0
            while b != len(blocks):
                # check if the last_term is the same as the last_term for the block
                if last_term == last_terms[b]:
                    f = blocks[b]
                    chunk = f.readlines(self.merge_chunk_size)
                    # if the file ends it needs to be removed from the lists
                    if not chunk:
                        f.close()
                        del blocks[b]
                        del last_terms[b]
                        continue

                    for term_postings in chunk:
                        term, *postings = term_postings.strip().split(' ')

                        postings_str = ""
                        for i in range(len(postings)):
                            postings[i] = PostingInfo.create(postings[i])
                            if self.ranking.name == "BM25":
                                postings[i].weight = self.__calculate_ci(
                                    term, postings[i].doc_id, postings[i].term_freq)
                            postings[i].term_freq = None
                            postings_str += f" {postings[i].write_to_index()}"
                        curr += i

                        terms.setdefault(term, ["", 0])
                        terms[term][0] += postings_str
                        terms[term][1] += i
                    last_terms[b] = term
                b += 1

            # last_term is only updated if the list is not empty
            last_term = min(last_terms) if last_terms else last_term

            if curr < self.merge_threshold and blocks:
                continue

            total = 0
            sorted_terms = sorted(terms)
            for term in sorted_terms:
                if term >= last_term:
                    break
                total += terms[term][1]
                if total >= self.merge_threshold:
                    break

            if total >= self.merge_threshold:
                # write when the total terms postings exceed a threshold
                curr -= total
                self.__store_term_merged_file(terms, sorted_terms, term, True)
            elif not blocks:
                # write the left terms in the last block
                self.__store_term_merged_file(terms, sorted_terms, term)

        self.clear_blocks()

    def __store_term_merged_file(self, terms, sorted_terms, last_term, threshold_term=False):
        """Write the terms in memory to an index file."""

        logging.info(f"Writing index \"{sorted_terms[0]} {last_term}\" to disk")     
        with self.open_merge_file(f"{self.merge_dir}{sorted_terms[0]} {last_term}.txt") as f:
            for ti, t in enumerate(sorted_terms):
                if not threshold_term or t <= last_term:
                    f.write(f"{t}{terms[t][0]}\n")
                    if self.file_location_step and ti % self.file_location_step == 0:
                        self.term_info[t].position = ti + 1
                    del terms[t]

    def __next_doc_id(self):
        """Get the next alias for the document ID"""

        # range of alias' alphabet in the ascii table
        max_char = 126
        min_char = 48

        doc_id = list(self.__last_rename) or list(chr(min_char))
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

        self.__last_rename = "".join(doc_id)
        return self.__last_rename

    def __calculate_ranking_info(self, terms, doc):
        """Calculate the ranking info"""

        if not self.ranking:
            return

        terms_cnt = {}
        for term, pos in terms:
            terms_cnt.setdefault(term, 0)
            terms_cnt[term] += 1

        if self.ranking.name == "VSM":
            cos_norm = 0

            for term in terms_cnt:
                self.term_doc_weights.setdefault(term, {})
                self.term_frequency.setdefault(term, {})

                cnt = terms_cnt[term]
                self.term_frequency[term][doc] = cnt
                if self.ranking.p1[0] == "l":
                    # l**
                    self.term_doc_weights[term][doc] = 1 + math.log10(cnt)
                elif self.ranking.p1[0] == "n":
                    # n**
                    self.term_doc_weights[term][doc] = cnt

                cos_norm += self.term_doc_weights[term][doc]**2

            if self.ranking.p1[2] == "c":
                # **c
                cos_norm = 1 / math.sqrt(cos_norm)
                for term in terms_cnt:
                    self.term_doc_weights[term][doc] *= cos_norm

        elif self.ranking.name == "BM25":
            self.document_lens[doc] = len(terms)
            self.__total_doc_lens += len(terms)

            for term in terms_cnt:
                self.term_frequency.setdefault(term, {})
                self.term_frequency[term][doc] = terms_cnt[term]

    def index_terms(self, terms, doc):
        """
        Index a list of terms provided by the tokenizer.

        @param terms: the list of terms
        @param doc: the document ID
        """
        # indexes a list of terms provided by the tokenizer

        if self.rename_doc:
            self.__next_doc_id()
            self.doc_ids[self.__last_rename] = doc
            doc = self.__last_rename

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
                self.__n_doc_indexed += 1

        if self.ranking:
            self.__calculate_idf()

        self.merge_block_disk()
        self.write_term_info_disk()
        if self.rename_doc:
            self.write_doc_ids()
        self.write_indexer_config()

    def __calculate_idf(self):
        """Calculate inverse document frequency for each term."""

        for term in self.term_info:
            document_frequency = self.term_info[term].posting_size
            idf = math.log10(self.__n_doc_indexed / document_frequency)
            self.term_info[term].idf = idf

    def __calculate_ci(self, term, doc, term_frequency):
        """Calculate BM25 weights for each term-doc."""

        avdl = self.__total_doc_lens / self.__n_doc_indexed
        idf = self.term_info[term].idf
        document_len = self.document_lens[doc]

        ci = idf * (self.ranking.k1 + 1) * term_frequency / (self.ranking.k1 *
            ((1 - self.ranking.b) + self.ranking.b * document_len/avdl) + term_frequency)

        return ci
