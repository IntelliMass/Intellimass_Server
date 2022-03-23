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

TOPICS_NUM = 1


class LdaModeling:
    def __init__(self, df_articles: pd.DataFrame):
        self._lda_model = None
        self.__papers = df_articles
        self._dict_of_topics = {}
        self._topics_list = []
        self._num_of_clusters = 4
        self._current_cluster = None

        self.__stopwords_string()
        self.__remove_punctuation_and_convert_to_lowercase()
        self.__prepare_data()
        self.kmeans_papers()
        self.activate_lda_training()

    def __remove_punctuation_and_convert_to_lowercase(self):
        print("__remove_punctuation_and_convert_to_lowercase")
        self.__papers['processed_abstract'] = self.__papers['abstract'].map(lambda x: re.sub('[,\.()!?]', '', x))
        self.__papers['processed_abstract'] = self.__papers['processed_abstract'].map(lambda x: x.lower())

    @staticmethod
    def __sent_to_words(sentences):
        print("__sent_to_words")
        for sentence in sentences:
            # deacc=True removes punctuations
            yield gensim.utils.simple_preprocess(str(sentence), deacc=True)

    def __stopwords_string(self):
        print("__stopwords_string")
        nltk.download('stopwords')
        self.stop_words = stopwords.words('english')
        self.stop_words.extend(['from', 'subject', 're', 'edu', 'use'])

    def remove_stopwords(self, word_list):
        return [word for word in word_list if word not in self.stop_words]

    def __prepare_data(self):
        print("__prepare_data")
        self.__papers['list_abstract'] = self.__papers['processed_abstract'].apply(lambda x: x.split())
        self.__papers['cleaned_abstract'] = self.__papers['list_abstract'].map(lambda x: self.remove_stopwords(x))
        self.__papers = self.__papers.drop(labels=['processed_abstract', 'list_abstract'], axis=1)
        self.__papers['clean_abstract_str'] = self.__papers['cleaned_abstract'].map(lambda x: " ".join(x))

    def kmeans_papers(self):
        print('kmeans_papers')
        vectorizer = TfidfVectorizer(sublinear_tf=True, min_df=5, max_df=0.95)
        x = vectorizer.fit_transform(self.__papers['clean_abstract_str'])
        kmeans = KMeans(n_clusters=self._num_of_clusters, random_state=42)
        kmeans.fit(x)
        clusters = kmeans.labels_
        self.__papers['categories'] = clusters

        # initialize PCA with 2 components
        pca = PCA(n_components=2, random_state=42)
        # pass X to the pca
        pca_vecs = pca.fit_transform(x.toarray())
        # save the two dimensions in x0 and x1
        x0 = pca_vecs[:, 0]
        x1 = pca_vecs[:, 1]
        self.__papers['x0'] = x0
        self.__papers['x1'] = x1

    def activate_lda_training(self):
        print('activate_lda_training')
        list_clusters_numbers = self.__papers['categories'].unique()
        for num in list_clusters_numbers:
            filtered_data = self.__papers[self.__papers["categories"] == num]
            # Create Dictionary
            id2word = corpora.Dictionary(filtered_data['cleaned_abstract'])
            # Create Corpus
            texts = filtered_data['cleaned_abstract']
            # Term Document Frequency
            corpus = [id2word.doc2bow(text) for text in texts]
            self._current_cluster = num
            self.__lda_model_training(corpus, id2word)
        self.__papers = self.__papers.drop(labels=['cleaned_abstract', 'clean_abstract_str', 'x0', 'x1'], axis=1)

    def __lda_model_training(self, corpus, id2word, num_topic=TOPICS_NUM):
        # Build LDA model
        self._lda_model = gensim.models.LdaMulticore(corpus=corpus, id2word=id2word, num_topics=num_topic)
        self.__topics_to_dict()

    def __topics_to_dict(self):
        for index in range(TOPICS_NUM):
            for topic in self._lda_model.show_topic(index):
                if topic[0] not in self._dict_of_topics:
                    self._dict_of_topics[topic[0]] = topic[1]
                else:
                    self._dict_of_topics[topic[0]] += topic[1]
        self.__top_topics()
        self._dict_of_topics = {}

    def __top_topics(self):
        temp_topic_list = sorted(self._dict_of_topics, key=self._dict_of_topics.get,
                                 reverse=True)[:self._num_of_clusters]
        for index in range(self._num_of_clusters):
            if temp_topic_list[index] not in self._topics_list:
                self._topics_list.append(temp_topic_list[index])
                self.__papers['categories'] = self.__papers['categories'].replace(self._current_cluster,
                                                                                  temp_topic_list[index])
                break

    @property
    def topics_list(self):
        return self._topics_list

    @property
    def papers(self):
        return self.__papers

    @property
    def clean_papers(self):
        return self.__papers['clean_abstract_str']