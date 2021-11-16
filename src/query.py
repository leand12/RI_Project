import logging

logging.basicConfig(level=logging.DEBUG, format='%(filename)s:%(lineno)d %(asctime)s - %(message)s', datefmt='%H:%M:%S')

class Query:

    def __init__(self, indexer):
        self.indexer = indexer

    def and_query(self, **args):
        pass

    def or_query(self, **args):
        ...

    def search(self, query):

        terms = self.indexer.tokenizer.normalize_tokens(query.strip().split())
        sizes = [self.indexer.term_info[term][0] if self.indexer.term_info[term] else 0 for term in terms ]
        terms = zip(terms, sizes)
        print(terms)

        temp = {}

        while len(terms) != 1:
            terms.sort(key=lambda x: x[1])
            t1, s1 = terms.pop()
            t2, s2 = terms.pop()

            if not s1 or not s2:
                logging.info("No results found")
                break

            if t1 not in temp:
                l1 = self.indexer.read_posting_lists(t1)
            else:
                l1 = temp[t1]

            if t2 not in temp:
                l2 = self.indexer.read_posting_lists(t2)
            else:
                l2 = temp[t2]

            n_term = t1 + " " + t2
            temp[n_term] = set(l1) & set(l2)
            terms.append((n_term, len(temp[n_term])))
        
