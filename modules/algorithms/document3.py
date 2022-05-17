import time
import json

import pandas as pd
import re
import gensim
import gensim.corpora as corpora
import nltk
from nltk.corpus import stopwords

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
import string

nltk.download('stopwords')
stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])


class TextSimilarity:

    def __init__(self, articles_df: pd.DataFrame, feature='abstract'):
        self.__texts_list = articles_df[feature]
        self.__clean_text()

    def __clean_text(self):
        self.__texts_list.map(lambda text: text.translate(str.maketrans('', '', string.punctuation)))
        self.__texts_list.map(lambda text: text.lower())

    def __prepare_data(self):
        self.__texts_list = self.__texts_list.map(lambda text: text.split())
        self.__texts_list = self.__texts_list.map(lambda text: text.split())
        self.__texts_list = self.__texts_list.map(lambda text: "".join(text))

    def __lda_training(self):
        id2word = corpora.Dictionary(self.__texts_list)
        corpus = [id2word.doc2bow(text) for text in self.__texts_list]
        self._lda_model = gensim.models.LdaMulticore(corpus=corpus, id2word=id2word, num_topics=10)
        self.__lda_model_training(corpus, id2word)
        print(self._lda_model.show_topic())




start = time.time()
print(f"lOAD TIME: { time.time() - start}")

with open('quantum1.txt') as f:
    quantum1 = f.read()

with open('quantum2.txt') as f:
    quantum2 = f.read()

with open('cyber.txt') as f:
    cyber = f.read()

with open('vitamins.txt') as f:
    vitamins = f.read()

import requests
import json
import pandas as pd

res = requests.get('http://ec2-35-178-32-52.eu-west-2.compute.amazonaws.com:5000/articles?id=d4fb1f03-8af5-414c-bc2d-16fd5b819a16&count=100&filters=&clusters=&numOfClusters=4')

articles = pd.DataFrame(json.loads(res.text)['articles'])
print(articles)
textsim = TextSimilarity(articles)
