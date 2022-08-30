from sentence_transformers import SentenceTransformer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import time


class BertTextSimilarity:
    """
    The model is not in use due to processing power issues.

    BERT is an open source machine learning framework for natural language processing (NLP).
    BERT is designed to help computers understand the meaning of ambiguous language in text
    by using surrounding text to establish context.
    The BERT framework was pre-trained using text from Wikipedia and can be fine-tuned with
    question and answer datasets.
    """
    model = SentenceTransformer('bert-base-nli-mean-tokens')

    def __init__(self, articles_df: pd.DataFrame, feature):
        if feature not in articles_df.columns:
            raise ValueError(f"{feature} not in DataFrame")
        if type(articles_df[feature][0]) != str:
            raise ValueError(f"articles_df[{feature}] is not str type.")
        self.text_series = articles_df[feature]
        self.start = time.time()

    def get_similarities(self):
        """

        :return: similarity matrix nXn. n=Number of compared articles
        """
        text_embeddings = self.model.encode(self.text_series)
        cos_sim = cosine_similarity(
            text_embeddings,
            text_embeddings
        )

        return cos_sim
