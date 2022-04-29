import sys
import os
from flask import Flask, Response
from flask_cors import CORS
import time
import json

###################################################
# MODULES MODULES MODULES MODULES MODULES MODULES #
from modules import utils
from modules.thirdParty import SemanticScholarAPI, config
from modules.db import sessionsTable, privateCollectionsTable
# MODULES MODULES MODULES MODULES MODULES MODULES #
###################################################

app = Flask(__name__)
CORS(app)


@app.route('/query', methods=['POST'])
def query():
    """
    Steps:
        1. Get articles from 3rd party
            rawArticles class :     {
                                        title: str,authors: list[str],
                                        isOpenAccess: bool,
                                        fieldsOfStudy: list[str],
                                        year: int,
                                        abstract: str,
                                        venue: str
                                    }
        2. Append to each article frequent words & topics.
    :response: 200/400
    """

    start = time.time()
    query = utils.getPostData('query')
    rawArticles = SemanticScholarAPI.getArticles(query)
    extendedArticles = utils.articleExtender(rawArticles, query)
    object = QueryObject(query, extendedArticles, config.Defaults.numOfArticles_firstSearch)
    db.insert(object)

    headers = {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*'
    }

    ################################################
    print("time: " + str(time.time() - start))
    ################################################

    return Response(response=json.dumps({'queryId': object.id}), status=200, headers=headers)



@app.route('/articles', methods=['GET'])
def get_articles():
    queryParams = utils.getQueryParams()

@app.route('/metadata', methods=['GET'])
def get_metadata():
    pass

@app.route('/network', methods=['GET'])
def get_network():
    pass

@app.route('/getOne', methods=['GET'])
def getOne():
    pass

@app.route('/categories', methods=['GET'])
def get_categories():
    pass



if __name__ == '__main__':

    ##################################################################
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    from waitress import serve
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'prod':
        serve(app, host="0.0.0.0", port=5000)
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    ##################################################################
    else:
        app.run(host='0.0.0.0', debug=True, port=int(os.environ.get("PORT", 5000)))
