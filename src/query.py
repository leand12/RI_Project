# Bruno Bastos 93302
# Leandro Silva 93446
import math
import logging
import os


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
            for i, line in enumerate(f):
                results = self.search(line)
                with open(f"./results.txt", "a+") as q:
                    q.write(f"Q: {line}\n")
                    for doc, score in results:
                        q.write(f"{doc}\t{score:.6f}\n")
                    q.write("\n")

    def search(self, query):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())

        if not terms:
            # FIXME: this stops the search while true, which is bad, 
            # maybe change to throw expection and handle it on main.py
            assert False, "The provided query is not valid"

        if self.indexer.ranking.name == "VSM":
            return self.tf_idf_score(terms)[:10]
        elif self.indexer.ranking.name == "BM25":
            return self.bm25_score(terms)[:10]
        # FIXME: return something when there is no ranking

    def tf_idf_score(self, terms):

        scores = {}
        cos_norm = 0
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                idf, weights, postings = term_info

                tf = terms.count(term)  # n**
                dc = 1                  # *n*

                if self.indexer.ranking.p2[0] == 'l':
                    # l**
                    tf = 1 + math.log10(tf)

                if self.indexer.ranking.p2[1] == 't':
                    # *t*
                    dc = float(idf)

                lt = tf * dc
                cos_norm += lt**2
                for i, doc in enumerate(postings):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * lt * terms.count(term)

        if scores:
            if self.indexer.ranking.p2[2] == 'c':
                # **c
                cos_norm = 1 / math.sqrt(cos_norm)
                for doc in scores:
                    scores[doc] *= cos_norm
            return sorted(scores.items(), key=lambda x: -x[1])

    def bm25_score(self, terms):

        scores = {}
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                _, weights, postings = term_info

                for i, doc in enumerate(postings):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * terms.count(term)

        if scores:
            return sorted(scores.items(), key=lambda x: -x[1])
