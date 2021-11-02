from nltk.stem import PorterStemmer
import os
import re
# https://towardsdatascience.com/text-normalization-7ecc8e084e31
# https://towardsdatascience.com/text-normalization-for-natural-language-processing-nlp-70a314bfa646

class Review:
    ID = 2
    HEADLINE = 11
    BODY = 12

class Tokenizer:
    
    def __init__(self, min_length=2, use_stopwords=True, use_stemmer=True):
        self.min_length = min_length
        self.stopwords = {}
        if use_stopwords:
            dirname, _ = os.path.split(os.path.abspath(__file__))
            self.stopwords = {w for w in open(dirname + "/../data/nltk_en_stopwords.txt", "r").read().split()}
        if use_stemmer:
            self.stemmer = PorterStemmer()

    def normalize_token(self, word):
        return re.sub('[^0-9a-zA-Z-_\']+', '', word.lower())

    def is_stopword(self, token):
        if token in self.stopwords:
            return True

        # TODO: stopwords
        return len(token) < 3

    def tokenize(self, line):
        doc = line.split('\t')
        review = doc[Review.HEADLINE] + doc[Review.BODY]
        review_id = doc[Review.ID]

        #self.update_fields(doc)
        terms = []
        for pos, token in enumerate(review.split()):
            term = self.normalize_token(token)

            if self.is_stopword(term):
                continue
            terms.append(term)
        # { token: { doc1: p1, p2} }
        # FIXME: change the return value
        # it is only like this to match the indexer
        return terms, review_id

#t = Tokenizer()
# ps_stem_sent = [ps.stem(words_sent) for words_sent in sent]
# print(ps_stem_sent)
