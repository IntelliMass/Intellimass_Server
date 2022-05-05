from sentence_transformers import SentenceTransformer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import time


class BertTextSimilarity:
    model = SentenceTransformer('bert-base-nli-mean-tokens')

    def __init__(self, articles_df: pd.DataFrame, feature):
        if type(articles_df[feature][0]) != str:
            raise ValueError(f"articles_df[{feature}] is not str type.")
        self.text_series = articles_df[feature]
        self.start = time.time()

    def get_similarities(self):
        text_embeddings = self.model.encode(self.text_series)
        cos_sim = cosine_similarity(
            text_embeddings,
            text_embeddings
        )

        return cos_sim
