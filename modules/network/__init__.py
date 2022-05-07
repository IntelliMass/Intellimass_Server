import threading
import time
import pandas as pd
import itertools
from modules.algorithms import BertTextSimilarity
import numpy as np

class Network:

    DEFAULT_THRESHOLD = 0.5
    ABSTRACT_MULTIPLIER_FOR_DEFAULT = 0.6
    TITLE_MULTIPLIER_FOR_DEFAULT = 0.4
    ABSTRACT_THRESHOLD = 0.5
    TITLE_THRESHOLD = 0.8

    def __init__(self, articles_df: pd.DataFrame, feature: str):
        self.network = None
        feature = feature.lower().replace(' ', '').lower()
        self.articles_df = articles_df

        eval(f"self.connect_by_{feature}()")

    def get_network(self):
        return self.network

    @staticmethod
    def __normalize(array):
        norm = np.linalg.norm(array)
        normalized_array = array / norm
        return normalized_array


    def __get_default_similarity(self, similarity_rank_title, similarity_rank_abstract):
        return similarity_rank_title * self.TITLE_MULTIPLIER_FOR_DEFAULT + \
        similarity_rank_abstract * self.ABSTRACT_MULTIPLIER_FOR_DEFAULT

    def connect_by_default(self):
        abstract_similarities = []
        thread_abstract = threading.Thread(target=self.connect_by_abstract, args=(abstract_similarities,))
        title_similarities = []
        thread_title = threading.Thread(target=self.connect_by_title, args=(title_similarities,))
        thread_abstract.start()
        thread_title.start()
        thread_abstract.join()
        thread_title.join()
        for i in range(len(abstract_similarities)):
            for j in range(len(abstract_similarities)):
                similarity = self.__get_default_similarity(title_similarities[i][j], abstract_similarities[i][j])
                if similarity > self.DEFUALT_THRESHOLD:
                    self.network.append(
                        {
                            "source": self.articles_df['paperId'][i],
                            "target": self.articles_df['paperId'][j],
                            "value": float("{:.4f}".format(similarity))
                        }
                    )

    def connect_by_abstract(self, call_back_object=None):
        self.network = []
        bert = BertTextSimilarity(self.articles_df, 'abstract')
        start = time.time()
        similarities = bert.get_similarities()
        similarities = self.__normalize(similarities)
        if call_back_object is not None:
            call_back_object = similarities
            print(f"Abstract Network takes {time.time() - start} seconds")
            return
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if ((call_back_object is not None) or (similarity > self.ABSTRACT_THRESHOLD)) and i != j:
                    self.network.append(
                        {
                            "source": self.articles_df['paperId'][i],
                            "target": self.articles_df['paperId'][j],
                            "value": float("{:.4f}".format(similarity))
                        }
                    )
        print(f"Abstract Network takes {time.time()-start} seconds")
        print(f"number of connections = {len(self.network)}")

    def connect_by_title(self, call_back_object=None):
        self.network = []
        bert = BertTextSimilarity(self.articles_df, 'title')
        start = time.time()
        similarities = bert.get_similarities()
        similarities = self.__normalize(similarities)
        if call_back_object is not None:
            call_back_object = similarities
            print(f"Title Network takes {time.time() - start} seconds")
            return
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if ((call_back_object is not None) or (similarity > self.ABSTRACT_THRESHOLD)) and i != j:
                    self.network.append(
                        {
                            "source": self.articles_df['paperId'][i],
                            "target": self.articles_df['paperId'][j],
                            "value": float("{:.4f}".format(similarity))
                        }
                    )
        print(f"Title Network takes {time.time() - start} seconds")
        print(f"number of connections = {len(self.network)}")

    def connect_by_authors(self):
        self.network = []
        start = time.time()
        for i, article1 in self.articles_df.iterrows():
            article_1_author_ids = [author['authorId'] for author in article1['authors']]
            for _, article2 in itertools.islice(self.articles_df.iterrows(), i + 1, None):
                if article1['paperId'] == article2['paperId']:
                    continue
                article_2_author_ids = [author['authorId'] for author in article2['authors']]
                common_authors_in_both_articles = list(set(article_1_author_ids).intersection(article_2_author_ids))
                common_authors_in_both_articles = [author['name'] for author in article1['authors'] if
                                               author['authorId'] in common_authors_in_both_articles]
                if len(common_authors_in_both_articles) > 0:
                    self.network.append(
                        {
                            "source": article1['paperId'],
                            "target": article2['paperId'],
                            "value": common_authors_in_both_articles
                        }
                    )
        print(f"Title Network takes {time.time() - start} seconds")
        print(f"number of connections = {len(self.network)}")



