import time

from semantic_network import SemanticNetwork
import json
import pandas as pd

with open("response.json") as f:
    network = json.load(f)
    articles = pd.DataFrame.from_records(network['network']['nodes'])

start = time.time()
SMnet = SemanticNetwork(articles)
print(SMnet.get_network())
print(f"Time: {time.time()- start}")