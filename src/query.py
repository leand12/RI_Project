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

class VS(Ranking):

    def __init__(self, p1="lnc", p2="ltc", **ignore):
        super().__init__("VS", p1, p2)

class BM25(Ranking):
    
    def __init__(self, k1=1.2, b=1, **ignore):
        super().__init__("BM25", k1, b)


class Query:

    def __init__(self, indexer):
        self.indexer = indexer

    def search_file(self, filename):
        if not os.path.exists("./queries"):
            os.mkdir("./queries")
        with open(filename, "r") as f:                
            for i, line in enumerate(f):
                results = self.search(line)
                with open("./queries/query" + str(i+1) + ".txt", "w+") as q:
                    for r in results:
                        q.write(f"{r[0]}\t{r[1]:.6f}\n")
                
    def search(self, query):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())

        if not terms:
            assert False, "The provided query is not valid"
        
        #sizes = [self.indexer.term_info[term][0] if self.indexer.term_info.get(term) else 0 for term in terms ]

        return self.tf_idf_score(terms)

    def tf_idf_score(self, terms):
        
        scores = {}
        cos_norm = 0
        for term in set(terms):
            if (term_info := self.indexer.read_posting_lists(term)):    
                idf, weights, postings = term_info
                lt = 1 + math.log10(terms.count(term)) * float(idf)
                cos_norm += (lt) ** 2
                for i, doc in enumerate(postings):
                    scores.setdefault(doc, 0)
                    scores[doc] += float(weights[i]) * (lt)

        if scores:
            cos_norm = 1 / math.sqrt(cos_norm)
            for doc in scores:
                scores[doc] *= cos_norm
            return sorted(scores.items(), key=lambda x: -x[1])[:100]
        
        
    def bm25_score(self, terms):
        
        pass
        