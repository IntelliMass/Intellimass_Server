import time

import pandas as pd
import itertools
from modules.algorithms import BertTextSimilarity

class Network:

    ABSTRACT_THRESHOLD = 0.5

    def __init__(self, articles_df: pd.DataFrame, feature: str):
        feature = feature.lower().replace(' ', '').lower()
        self.articles_df = articles_df
        self.network = []
        eval(f"self.connect_by_{feature}(dfOfArticles)")

    def get_network(self):
        return self.network

    def connect_by_default(self):
        pass

    def connect_by_abstarcts(self):
        links = []
        bert = BertTextSimilarity(self.articles_df, 'abstarct')
        start = time.time()
        similarities = bert.get_similarities()
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if similarity > self.ABSTRACT_THRESHOLD:
                    links.append(
                        {
                            "source": self.articles_df['paperId'][i],
                            "target": self.articles_df['paperId'][j],
                            "value": similarity
                        }
                    )
        print(f"Abstract Network takes {time.time()-start} seconds")

    def connect_by_titles(self):
        links = []
        bert = BertTextSimilarity(self.articles_df, 'title')
        start = time.time()
        similarities = bert.get_similarities()
        for i, similarities_array in enumerate(similarities):
            for j, similarity in enumerate(similarities_array):
                if similarity > self.ABSTRACT_THRESHOLD:
                    links.append(
                        {
                            "source": self.articles_df['paperId'][i],
                            "target": self.articles_df['paperId'][j],
                            "value": similarity
                        }
                    )
        print(f"Title Network takes {time.time() - start} seconds")


    def connect_by_authors(dfOfArticles: pd.DataFrame):
        links = []
        for i, article1 in dfOfArticles.iterrows():
            article_1_author_ids = [author['authorId'] for author in article1['authors']]
            for _, article2 in itertools.islice(dfOfArticles.iterrows(), i + 1, None):
                if article1['paperId'] == article2['paperId']:
                    continue
                article_2_author_ids = [author['authorId'] for author in article2['authors']]
                common_authors_in_both_articles = list(set(article_1_author_ids).intersection(article_2_author_ids))
                common_authors_in_both_articles = [author['name'] for author in article1['authors'] if
                                               author['authorId'] in common_authors_in_both_articles]
                if len(common_authors_in_both_articles) > 0:
                    links.append(
                        {
                            "source": article1['paperId'],
                            "target": article2['paperId'],
                            "value": common_authors_in_both_articles
                        }
                    )
        return links



