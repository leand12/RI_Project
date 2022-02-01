# Bruno Bastos 93302
# Leandro Silva 93446

import math
import logging
import os
from random import random
import time

from tabulate import tabulate
from utils import levenshtein
import numpy as np
from typing import List


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

    def __init__(self, indexer, window=5):
        self.indexer = indexer
        self.window_size = window

    def search_file(self, filename):

        with open(filename, "r") as f:
            with open(f"./results.txt", "w") as q:
                for i, line in enumerate(f):
                    line = line.strip()

                    start = time.perf_counter()
                    results = self.search(line)

                    logging.info(
                        f"{time.perf_counter() - start:.2f} sec to search for \"{line}\"")

                    q.write(f"Q: {line}\n\n")
                    if not results:
                        q.write(
                            "Your search - {line} - did not match any documents\n")
                        continue

                    for doc, score in results:
                        q.write(f"{doc}\t{score:.6f}\n")
                    q.write("\n")

    def search_file_with_accuracy(self, filename):

        all_data = []
        header = ["Top K", "Precision", "Recall",
                  "F-Measure", "Average Precision", "NDCG"]

        start = time.perf_counter()
        queries = 0
        with open(filename, "r") as f:

            for line in f:
                if line.startswith("Q:"):
                    queries += 1
                    query = line[2:].strip()
                    docs = []
                    while (line := f.readline().strip()):
                        temp = line.split()
                        docs.append((temp[0], int(temp[1])))

                    data = self.metrics(docs, self.search(query, top=50))
                    all_data.append(data)

        total_time = time.perf_counter() - start

        logging.info(
            f"Query Throughput: {queries / total_time:.2f} queries/second")
        logging.info(
            f"Query Execution Time: {total_time / queries:.2f} seconds/query")
        logging.info(
            f"Total time taken to search for all queries: {total_time:.2f} seconds")

        avg_data = np.array(all_data[0])
        for data in all_data[1:]:
            avg_data += np.array(data)
        avg_data /= len(all_data)

        print('\n', "Metrics for all queries")
        print(tabulate([header, *avg_data],
              headers="firstrow", floatfmt='.3f'))

    def search(self, query, top=10):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())

        if not terms:
            return None

        if self.indexer.ranking.name == "VSM":
            return self.tf_idf_score(terms)[:top]
        elif self.indexer.ranking.name == "BM25":
            return self.bm25_score(terms)[:top]

    def tf_idf_score(self, terms: List[str]):
        """Sort and rank the documents according to VSM"""

        scores = {}
        cos_norm = 0
        term_postings = {}
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                idf, weights, postings = term_info
                term_postings[term] = postings
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
                for i, doc in enumerate(postings.keys()):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * lt * cnt

        if scores:
            if self.indexer.ranking.p2[2] == 'c':
                # normalization (cosine) **c
                cos_norm = 1 / math.sqrt(cos_norm)
                for doc in scores:
                    scores[doc] *= cos_norm
            scores = self.boost_query(terms, term_postings, scores)
            return sorted(scores.items(), key=lambda x: -x[1])

    def bm25_score(self, terms: List[str]):
        """Sort and rank the documents according to BM25"""

        scores = {}
        term_postings = {}
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):
                _, weights, postings = term_info
                term_postings[term] = postings
                cnt = term.count(term)
                for i, doc in enumerate(postings.keys()):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * cnt
        if scores:
            scores = self.boost_query(terms, term_postings, scores)
            return sorted(scores.items(), key=lambda x: -x[1])

    def boost_query(self, terms: List[str], term_postings, scores):

        positions = {}
        for doc in scores:
            positions[doc] = []
            for term in term_postings:
                if doc in term_postings[term]:
                    positions[doc].extend(
                        [(term, int(pos)) for pos in term_postings[term][doc]]
                    )

            positions[doc].sort(key=lambda x: x[1])

        for doc in positions:
            d_pos = positions[doc]
            boost = 0
            # slide window so that it starts on query token
            for i in range(len(d_pos)):
                window = [None] * self.window_size
                window[0] = d_pos[i][0]

                tempi = i
                start = d_pos[i][1]
                while i + 1 < len(d_pos) and d_pos[i + 1][1] - start < self.window_size:
                    window[d_pos[i + 1][1] - start] = d_pos[i + 1][0]
                    i += 1

                if i > tempi:
                    if len(set(window)) <= 2:
                        continue

                    while window[-1] == None:
                        window.pop()

                    boost += self.__evaluate_window(terms, window)

            score = 0.8 * boost / len(d_pos)**2
            scores[doc] += scores[doc] * score

        # print('\n'.join(b[0] + '\t' + str(b[1]) for b in sorted(all_boost, key=lambda x: x[1])))
        # print('\n'*4)
        return scores

    def __evaluate_window(self, terms, window):

        # n de termos na query
        count = len(set(x for x in window if x))  # windowsize
        # count += 0.1 * (sum(1 for x in window if x) - count + 1)
        count += len(terms) - levenshtein(terms, window)

        return (count / (len(window) + len(terms)))**(1 if self.indexer.ranking.name == "VSM" else 2)

    def metrics(self, real, predicted):

        data = []
        real_docs = set(doc for doc, _ in real)
        for k in (10, 20, 50):
            precisions = []
            rankings = []
            tp = 0
            for i, (doc, score) in enumerate(predicted[:k]):
                rankings.append(0)

                for d, s in real:
                    if d == doc:
                        tp += 1
                        rankings[-1] = s
                        break

                precisions.append(tp/(i+1))

            idcg = real[0][1] + sum(r[1] / math.log2(i + 2)
                                    for i, r in enumerate(real[1:k]))
            dcg = rankings[0] + sum(r / math.log2(i + 2)
                                    for i, r in enumerate(rankings[1:]))
            ndcg = dcg / idcg if idcg else 0

            fp = k - tp

            fn = len(real_docs) - tp

            # Precision = TP / TP + FP
            precision = tp / (tp + fp)

            # Recall = TP / TP + FN
            recall = tp / (tp + fn)

            # F-Measure = 2RP / (R + P)
            f1_score = 2 * recall*precision / \
                (recall + precision) if precision or recall else 0

            avg_precisions = sum(precisions) / len(precisions)

            data.append([k, precision, recall, f1_score, avg_precisions, ndcg])

        return data
