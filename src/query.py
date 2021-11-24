# Bruno Bastos 93302
# Leandro Silva 93446
import math
import logging

class Query:

    def __init__(self, indexer):
        self.indexer = indexer

    def and_query(self, **args):
        pass

    def or_query(self, **args):
        ...

    def search(self, query):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())

        if not terms:
            assert False, "nothing"
        
        sizes = [self.indexer.term_info[term][0] if self.indexer.term_info.get(term) else 0 for term in terms ]
        #terms = list(zip(terms, sizes))
        print(terms)
        temp = {}

        scores = {}
        cos_norm = 0
        w_terms = {}
        for term in set(terms):
            if not (term_info := self.indexer.read_posting_lists(term)):
                continue
            idf, weights, postings = term_info
            l = 1 + math.log10(terms.count(term)) # no. de terms no documento
            t = float(idf)
            cos_norm += (l * t) ** 2
            w_terms[term] = (l * t)
            for i, doc in enumerate(postings):
                scores.setdefault(doc, 0)
                scores[doc] += float(weights[i]) * w_terms[term]

        if scores:
            cos_norm = 1 / math.sqrt(cos_norm)
            for doc in scores:
                scores[doc] *= cos_norm
            print([(k, v) for k, v in sorted(scores.items(), key=lambda x: -x[1])])
            return scores
        """
        
        # and is not longer required
        while len(terms) > 1:
            terms.sort(key=lambda x: -x[1])
            t1, s1 = terms.pop()
            t2, s2 = terms.pop()
            print(terms)

            if not s1 or not s2:
                return None

            if t1 not in temp:
                l1 = set(self.indexer.read_posting_lists(t1))
            else:
                l1 = temp[t1]

            if t2 not in temp:
                l2 = set(self.indexer.read_posting_lists(t2))
            else:
                l2 = temp[t2]

            n_term = t1 + " " + t2
            temp[n_term] = l1 & l2
            terms.append((n_term, len(temp[n_term])))
        
        if terms and terms[0][1]:
            if terms[0][0] not in temp:
                l1 = set(self.indexer.read_posting_lists(terms[0][0]))
            else:
                l1 = temp[terms[0][0]]
            print(l1)
            return l1
        return None
        """