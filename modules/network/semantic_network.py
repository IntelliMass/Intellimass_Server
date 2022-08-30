import math
from collections import Counter
import pandas as pd
from nltk.tokenize import word_tokenize
from string import punctuation
import re
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
stop_words = stopwords.words('english')
lemma = nltk.wordnet.WordNetLemmatizer()

MY_STOP_WORDS = ['', 'etc', '-', 'the', 'and', 'for', 'this', 'that', 'are', 'with', 'its', 'these', 'thing', 'also', 'thus', ]


class SemanticNetwork:

    def __init__(self, articles_df: pd.DataFrame):
        self.articles_df = articles_df
        self.abstracts = articles_df['abstract']
        self.words = None
        self.sentences = None
        self.links = []
        self.pre_process()
        self.link_network()

    @staticmethod
    def __preprocess_text(text):
        text = text.lower()  # Lowercase text
        text = re.sub(f"[{re.escape(punctuation).replace('.', '')}]", "", text)  # Remove punctuation
        text = " ".join(text.split())  # Remove extra spaces, tabs, and new lines
        return text

    def __abstract_to_sentences(self):
        tmp_sentences = []
        for abstract in self.abstracts:
            abstract = self.__preprocess_text(abstract)
            abstract = ' '.join([lemma.lemmatize(word) for word in abstract.split() if word not in stop_words and word not in MY_STOP_WORDS])
            tmp_sentences.extend(abstract.split('.'))

        tmp_sentences = [sentence.strip() for sentence in tmp_sentences if sentence.count(' ') > 2]
        self.sentences = [re.sub(r'\b\w{1,2}\b', '', sentence) for sentence in tmp_sentences]

    def __sentences_to_words(self):
        self.words = []
        for sentence in self.sentences:
            t_words = sentence.split(' ')
            self.words.extend(t_words)

        self.words = list(filter(lambda word: word != '', self.words))
        counted = Counter(self.words)
        self.words = counted.most_common(100)
        self.nodes = [{"title": word[0], "size": 5 * word[1]} for word in self.words]

    def pre_process(self):
        self.__abstract_to_sentences()
        self.__sentences_to_words()

    def link_network(self):
        t_links = []
        for i, (word1, _) in enumerate(self.words):
            for sentence in self.sentences:
                if word1 in sentence:
                    for word2, _ in self.words[i:]:
                        if word1 != word2 and word1 in sentence and word2 in sentence:
                            t_links.append((word1, word2))


        counted = Counter(t_links)
        counted = counted.most_common(math.floor(len(counted) / 10))
        for link, value in counted:
            self.links.append({
                "source": link[0],
                "target": link[1],
                "size": value / 5
            })

    def get_network(self):
        return self.nodes, self.links
