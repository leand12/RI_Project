import re
import sys

PRODUCT_TITLE = 5
REVIEW_HEADLINE = 11
REVIEW_BODY = 12
REVIEW_ID = 2

class Indexer:
    
    def __init__(self, save_positions=False):
        self.save_positions = save_positions  # the user might want to specify whether or not it wants
                                              # to save the positions of each term in a doc
        self.indexer = {}
        self.term_size = {}
        self.fields = {"title": {}, "headline": {}, "body": {}} # keeps the positions of the title, etc of each doc
        

    def print_indexer(self, max_entries=1000):
        for word, docs in list(self.indexer.items())[:max_entries]:
            if self.save_positions:
                a = ' '.join(str(x) for x in list(docs.items())[:5])
            else:
                a = ' '.join(str(x) for x in list(docs)[:5])

            print(f"{word:16s}  {len(docs):6d}  {a}")

    def normalize_word(self, word):
        return re.sub('[^0-9a-zA-Z-_\']+', '', word.lower())

    def is_stop_word(self, word):
        # TODO: stopwords
        return len(word) < 3

    def free_memory_available(self):
        return True

    def write_to_disk(self):
        pass

    def update_fields(self, doc):
        rid = doc[REVIEW_ID]

        title_size = len(doc[PRODUCT_TITLE].split())
        headline_size = len(doc[PRODUCT_TITLE].split())
        body_size = len(doc[PRODUCT_TITLE].split())
        self.fields["title"][rid] = (0, title_size)              # [0, title_size[
        self.fields["headline"][rid] = (title_size, headline_size)
        self.fields["body"][rid] = (headline_size, body_size)

    def update_index_entry(self, term, doc_id, n=None):
        """
        Needs the term, the id of the doc and the position of the term in the doc 
        """

        if self.save_positions:
            self.indexer.setdefault(term, {doc_id: []}) \
                    .setdefault(doc_id, []) \
                    .append(n)
        else:
            self.indexer.setdefault(term, [])
            self.indexer[term].append(doc_id)

    def save_term_size(self, term):
        # this function is called when docs are stored in disk    
        self.term_size[term] = len(self.indexer[term])


    def tokenizer(self, filename):
        fp = open(filename, "r")
        fp.readline()
        for line in fp:
            doc = line.split('\t')
            review = doc[PRODUCT_TITLE] + doc[REVIEW_HEADLINE] + doc[REVIEW_BODY]
            doc_id = doc[REVIEW_ID]

            self.update_fields(doc)

            for w, word in enumerate(review.split()):
                term = self.normalize_word(word)

                if self.is_stop_word(term):
                    continue

                self.update_index_entry(term, doc_id, w)

        # { token: { doc1: p1, p2} }
        
        self.print_indexer()

        fp.close()


indexer = Indexer()
indexer.tokenizer("data")




"""
# Search
token = "."
while token:
    token = input("Search: ")
    token = normalize_word(token)
    reviews = indexer[token]
    for title, headline, body in reviews:
        print(title)
        print(headline)
        print(body)
"""