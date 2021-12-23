# Bruno Bastos 93302
# Leandro Silva 93446
import math
import logging
import os
import time


class Ranking:

    def __init__(self, name, p1, p2):
        self.name = name
        self.p1 = p1
        self.p2 = p2


class VSM(Ranking):

    def __init__(self, p1="lnc", p2="ltc", **ignore):

        if len(p1) != 3 or p1[0] not in "ln" or p1[1] not in "n" or p1[2] not in "cn":
            logging.info(f"Configuration {p1} for the document is not implemented."
                         "Using default configuration: lnc")
            p1 = "lnc"

        if len(p2) != 3 or p2[0] not in "ln" or p2[1] not in "tn" or p2[2] not in "cn":
            logging.info(f"Configuration {p2} for the query is not implemented."
                         "Using default configuration: ltc")
            p1 = "ltc"

        super().__init__("VSM", p1, p2)


class BM25(Ranking):

    def __init__(self, k1=1.2, b=1, **ignore):
        assert 0 <= b <= 1, "The document length normalization, b, must be in [0, 1]"

        self.k1 = k1
        self.b = b
        super().__init__("BM25", k1, b)


class Query:

    def __init__(self, indexer):
        self.indexer = indexer

    def search_file(self, filename):
        
        with open(filename, "r") as f:
            with open(f"./results.txt", "w") as q:
                for i, line in enumerate(f):
                    line = line.strip()

                    start = time.perf_counter()
                    results = self.search(line)

                    logging.info(f"{time.perf_counter() - start:.2f} sec to search for \"{line}\"")
                    
                    q.write(f"Q: {line}\n\n")
                    if not results:
                        q.write("Your search - {line} - did not match any documents\n")
                        continue
                    
                    for doc, score in results:
                        q.write(f"{doc}\t{score:.6f}\n")
                    q.write("\n")

    def search(self, query):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())

        if not terms:
            return None

        if self.indexer.ranking.name == "VSM":
            return self.tf_idf_score(terms)[:100]
        elif self.indexer.ranking.name == "BM25":
            return self.bm25_score(terms)[:100]

    def tf_idf_score(self, terms):
        """Sort and rank the documents according to VSM"""

        scores = {}
        cos_norm = 0
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                idf, weights, postings = term_info
                cnt = terms.count(term)
                tf = cnt    # term frequency (natural) n**
                dc = 1      # document frequency (no) *n*

                if self.indexer.ranking.p2[0] == 'l':
                    # term frequency (logarithm) l**
                    tf = 1 + math.log10(tf)

                if self.indexer.ranking.p2[1] == 't':
                    # document frequency (idf) *t*
                    dc = float(idf)

                lt = tf * dc
                cos_norm += lt**2
                for i, doc in enumerate(postings):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * lt * cnt

        if scores:
            if self.indexer.ranking.p2[2] == 'c':
                # normalization (cosine) **c
                cos_norm = 1 / math.sqrt(cos_norm)
                for doc in scores:
                    scores[doc] *= cos_norm
            return sorted(scores.items(), key=lambda x: -x[1])

    def bm25_score(self, terms):
        """Sort and rank the documents according to BM25"""

        scores = {}
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                _, weights, postings = term_info
                cnt = term.count(term)
                for i, doc in enumerate(postings):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * cnt

        if scores:
            return sorted(scores.items(), key=lambda x: -x[1])
