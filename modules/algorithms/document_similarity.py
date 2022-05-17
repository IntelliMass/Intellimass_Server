import time
from re import sub
from gensim.utils import simple_preprocess
import requests




query_string = 'fruit and vegetables'
documents = ['cars drive on the road', 'tomatoes are actually fruit']

stopwords = ['the', 'and', 'are', 'a']


# From: https://github.com/RaRe-Technologies/gensim/blob/develop/docs/notebooks/soft_cosine_tutorial.ipynb
def preprocess(doc):
    # Tokenize, clean up input document string
    doc = sub(r'<img[^<>]+(>|$)', " image_token ", doc)
    doc = sub(r'<[^<>]+(>|$)', " ", doc)
    doc = sub(r'\[img_assist[^]]*?\]', " ", doc)
    doc = sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', " url_token ", doc)
    return [token for token in simple_preprocess(doc, min_len=0, max_len=float("inf")) if token not in stopwords]

# Preprocess the documents, including the query string
corpus = [preprocess(document) for document in documents]
query = preprocess(query_string)

import gensim.downloader as api
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.models import WordEmbeddingSimilarityIndex
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity

# Load the model: this is a big file, can take a while to download and open
glove = api.load("glove-wiki-gigaword-50")
similarity_index = WordEmbeddingSimilarityIndex(glove)

import time

# Build the term dictionary, TF-idf model
dictionary = Dictionary(corpus+[query])
tfidf = TfidfModel(dictionary=dictionary)

start = time.time()

# Create the term similarity matrix.
similarity_matrix = SparseTermSimilarityMatrix(similarity_index, dictionary, tfidf)

print(f"Time: {time.time() - start}")

print(similarity_matrix)