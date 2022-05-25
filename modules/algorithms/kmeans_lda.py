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
MY_STOP_WORDS = ['from', 'subject', 're', 'edu', 'use', 'things', 'smart', 'devices', 'new', 'proposed', 'try:based']


class LdaModeling:
    def __init__(self, df_articles: pd.DataFrame, search_keys: list, num_of_clusters=4):
        self._lda_model = None
        self.__papers = df_articles
        self._dict_of_topics = {}
        self._topics_list = []
        self._num_of_clusters = num_of_clusters
        self._current_cluster = None
        self._search_keyword = search_keys

        self.__stopwords_string()
        self.__remove_punctuation_and_convert_to_lowercase()
        self.__prepare_data()
        self.kmeans_papers()
        self.activate_lda_training()

    def __loading_and_cleaning_data(self, path: str):
        print("__loading_and_cleaning_data")
        if path.endswith('json'):
            loaded_json = json.load(open(path))
            self.__papers = pd.DataFrame(loaded_json['articles'])
        if path.endswith('csv'):
            self.__papers = pd.read_csv(path)

    def __remove_punctuation_and_convert_to_lowercase(self):
        print("__remove_punctuation_and_convert_to_lowercase")
        self.__papers.loc[:, 'processed_abstract'] = self.__papers.loc[:, 'abstract'].map(
            lambda x: re.sub('[,\.()!?]', '', x))
        self.__papers.loc[:, 'processed_abstract'] = self.__papers.loc[:, 'processed_abstract'].map(lambda x: x.lower())

    @staticmethod
    def __sent_to_words(sentences):
        print("__sent_to_words")
        for sentence in sentences:
            # deacc=True removes punctuations
            yield gensim.utils.simple_preprocess(str(sentence), deacc=True)

    def __stopwords_string(self):
        print("__stopwords_string")
        self.stop_words = stopwords.words('english')
        self.stop_words.extend(MY_STOP_WORDS)

    def remove_stopwords(self, word_list):
        return [word for word in word_list if word not in self.stop_words]

    def __prepare_data(self):
        print("__prepare_data")
        self.__papers.loc[:, 'list_abstract'] = self.__papers.loc[:, 'processed_abstract'].apply(lambda x: x.split())
        self.__papers.loc[:, 'cleaned_abstract'] = self.__papers.loc[:, 'list_abstract'].map(
            lambda x: self.remove_stopwords(x))
        self.__papers = self.__papers.drop(labels=['processed_abstract', 'list_abstract'], axis=1)
        self.__papers['clean_abstract_str'] = self.__papers.loc[:, 'cleaned_abstract'].map(lambda x: " ".join(x))

    def kmeans_papers(self):
        print('kmeans_papers')
        vectorizer = TfidfVectorizer(sublinear_tf=True, min_df=5, max_df=0.95)
        try:
            x = vectorizer.fit_transform(self.__papers['clean_abstract_str'])
        except ValueError:
            print(self.__papers['clean_abstract_str'])
            raise Exception("Empty (?)")
        kmeans = KMeans(n_clusters=self._num_of_clusters, random_state=42)
        kmeans.fit(x)
        clusters = kmeans.labels_
        self.__papers['cluster'] = clusters

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
        list_clusters_numbers = self.__papers['cluster'].unique()
        for num in list_clusters_numbers:
            filtered_data = self.__papers[self.__papers["cluster"] == num]
            # Create Dictionary
            id2word = corpora.Dictionary(filtered_data['cleaned_abstract'])
            # Create Corpus
            texts = filtered_data['cleaned_abstract']
            # Term Document Frequency
            corpus = [id2word.doc2bow(text) for text in texts]
            self._current_cluster = num
            self.__lda_model_training(corpus, id2word)
        self.__papers = self.__papers.drop(labels=['cleaned_abstract', 'clean_abstract_str', 'x0', 'x1'], axis=1)
        try:
            self.__papers['cluster'] = self.__papers['cluster'].apply(lambda cluster:
                                                                      cluster.capitalize() if cluster[
                                                                          0].islower() else cluster)
        except TypeError:
            print(set(self.__papers['cluster']))

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
                                 reverse=True)[:self._num_of_clusters + 2]
        print(temp_topic_list)
        for topic in temp_topic_list:
            if topic not in self._topics_list and topic not in self._search_keyword \
                    and topic + 's' not in temp_topic_list:
                valid_topic = topic
                for freq_words in set(self.__papers['frequentWords'].explode()):
                    if valid_topic == freq_words.lower():
                        valid_topic = freq_words
                        break
                self._topics_list.append(valid_topic)
                self.__papers['cluster'] = self.__papers['cluster'].replace(self._current_cluster,
                                                                            valid_topic)

    @property
    def topics_list(self):
        return self._topics_list

    @property
    def papers(self):
        return self.__papers

    @property
    def clean_papers(self):
        return self.__papers['clean_abstract_str']


def main():
    path_json = './json_file/response100_IOT.json'
    lda_temp = LdaModeling(path_json)
    topic_list = lda_temp.topics_list
    print(topic_list)
