import threading
import time
from collections import Counter

import pandas as pd
import itertools
from modules.algorithms import BertTextSimilarity
from modules.network.semantic_network import SemanticNetwork

class Network:

    DEFUALT_THRESHOLD = 0.5
    ABSTRACT_THRESHOLD = 0.5
    TITLE_THRESHOLD = 0.9

    def __init__(self, articles_df: pd.DataFrame, feature: str):
        self.network = None
        feature = feature.lower().replace(' ', '').lower()
        self.articles_df = articles_df
        if feature not in [column.lower() for column in self.articles_df.columns]:
            raise ValueError('feature not in DataFrame')
        self.count_connections_list = []
        eval(f"self.connect_by_{feature}()")
        TypeError(f"self.connect_by_{feature}()")
        try:
            self.count_connections()
        except Exception as ex:
            print(str(ex))

    def get_network(self):
        return self.articles_df, self.network

    def count_connections(self):
        temp_connections = []
        for node in self.network:
            temp_connections.append(node['source'])
            temp_connections.append(node['target'])

        temp_connections = dict(Counter(temp_connections))
        factor = 1.0 / max(temp_connections.values())
        for k in temp_connections.keys():
            temp_connections[k] = temp_connections[k] * factor
        basic_size = 200
        connections_full_size_factor = 200
        self.articles_df['size'] = [basic_size] * len(self.articles_df)
        for node, value in temp_connections.items():
            self.articles_df.loc[self.articles_df['title'] == node, 'size'] += connections_full_size_factor * value

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
            continue

    def connect_by_abstract(self, call_back_object=None):
        self.network = []
        bert = BertTextSimilarity(self.articles_df, 'abstract')
        start = time.time()
        similarities = bert.get_similarities()
        if call_back_object is not None:
            call_back_object = similarities
            print(f"Abstract Network takes {time.time() - start} seconds")
            return
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if ((call_back_object is not None) or (similarity > self.ABSTRACT_THRESHOLD)) and i != j:
                    t_link = {
                            "target": self.articles_df['title'][i],
                            "source": self.articles_df['title'][j],
                            "value": float("{:.4f}".format(similarity))
                        }
                    if t_link not in self.network:
                        self.network.append(
                            {
                                "source": self.articles_df['title'][i],
                                "target": self.articles_df['title'][j],
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
        if call_back_object is not None:
            call_back_object = similarities
            print(f"Title Network takes {time.time() - start} seconds")
            return
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if ((call_back_object is not None) or (similarity > self.ABSTRACT_THRESHOLD)) and i != j:
                    t_link = {
                        "target": self.articles_df['title'][i],
                        "source": self.articles_df['title'][j],
                        "value": float("{:.4f}".format(similarity))
                    }
                    if t_link not in self.network:
                        self.network.append(
                            {
                                "source": self.articles_df['title'][i],
                                "target": self.articles_df['title'][j],
                                "value": float("{:.4f}".format(similarity))
                            }
                        )
        print(f"Title Network takes {time.time() - start} seconds")
        print(f"number of connections = {len(self.network)}")

    def connect_by_frequentwords(self, call_back_object=None):
        self.network = []
        start = time.time()
        for i, article1 in self.articles_df.iterrows():
            for _, article2 in self.articles_df.iterrows():
                if article1['paperId'] == article2['paperId']:
                    continue
                common_freqwords_in_both_articles = list(set(article1['frequentWords']).intersection(article2['frequentWords']))
                common_freqwords_in_both_articles = sorted([freqword for freqword in article1['frequentWords'] if
                                               freqword in common_freqwords_in_both_articles])
                if len(common_freqwords_in_both_articles) > 1:
                    t_link = {
                        "target": article2['title'],
                        "source": article1['title'],
                    }
                    if t_link not in [{"target": link["target"], "source": link["source"]} for link in self.network]:
                        self.network.append(
                            {
                                "source": article1['title'],
                                "target": article2['title'],
                                "value": common_freqwords_in_both_articles
                            }
                        )
        print(f"frequentWords Network takes {time.time() - start} seconds")
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
                    t_link = {
                        "target": article2['title'],
                        "source": article1['title'],
                        "value": common_authors_in_both_articles
                    }
                    if t_link not in self.network:
                        self.network.append(
                            {
                                "source": article1['title'],
                                "target": article2['title'],
                                "value": common_authors_in_both_articles
                            }
                        )
        print(f"Authors Network takes {time.time() - start} seconds")
        print(f"number of connections = {len(self.network)}")
