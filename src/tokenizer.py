from nltk.stem import SnowballStemmer
import os
import re
# https://towardsdatascience.com/text-normalization-7ecc8e084e31
# https://towardsdatascience.com/text-normalization-for-natural-language-processing-nlp-70a314bfa646


class Review:
    ID = 2
    HEADLINE = 12
    BODY = 13


class Tokenizer:

    def __init__(self, case_folding=True, no_numbers=True, stemmer=True, min_length=3,
                 stopwords_file="../data/nltk_en_stopwords.txt", 
                 contractions_file="../data/en_contractions.txt"):

        self.min_length = min_length
        self.case_folding = case_folding
        self.no_numbers = no_numbers
        self.contractions = {}
        self.stopwords = set()
        self.stemmer = None
        path, _ = os.path.split(os.path.abspath(__file__))
        if stopwords_file:
            self.stopwords = {w.lower() for w in open(
                path + "/" + stopwords_file, "r").read().split()}
        if contractions_file:
            for line in open(path + "/" + contractions_file, "r"):
                token, term = line.lower().split(',')
                self.contractions[token] = term
        if stemmer:
            self.stemmer = SnowballStemmer("english")

    def normalize_tokens(self, terms):
        terms = [re.sub(r'[^a-zA-Z0-9]', ' ', term).split() for term in terms]
        terms = [term for subterms in terms for term in subterms]

        if self.min_length:
            terms = [term for term in terms if len(term) >= self.min_length]
        if self.stopwords:
            terms = [term for term in terms if term not in self.stopwords]
        if self.contractions:
            terms = [term if term not in self.contractions else self.contractions[term]
                     for term in terms]
        if self.no_numbers:
            terms = [term for term in terms if not term.replace(
                ',', '').replace('.', '').isdigit()]
        if self.case_folding:
            terms = [term.casefold() for term in terms]
        if self.stemmer:
            terms = [self.stemmer.stem(term) for term in terms]

        return terms

    def tokenize(self, line):
        doc = line.split('\t')
        review = doc[Review.HEADLINE] + " " + doc[Review.BODY]
        review_id = doc[Review.ID]

        # self.update_fields(doc)
        terms = []
        for pos, term in enumerate(self.normalize_tokens(review.split())):
            terms.append((term, str(pos)))
        # { token: { doc1: p1, p2} }
        # FIXME: change the return value
        # it is only like this to match the indexer
        return terms, review_id

#t = Tokenizer()
# ps_stem_sent = [ps.stem(words_sent) for words_sent in sent]
# print(ps_stem_sent)
