from flask import request, Response
import time
from config import db_conn


def common_api_get_request():
    queryId = request.args.get('id')
    if queryId is None:
        return Response(response="Bad Request - id",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    if queryId == "":
        return Response(response="Bad Request - id empty",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    print(queryId)
    count = request.args.get('count')
    if count is None:
        count = 100
    try:
        count = int(count)
    except TypeError:
        return Response(response="Bad Request - count", headers={'Access-Control-Allow-Origin': '*'}, status=200)

    start = time.time()
    while 1:
        obj = db_conn.sessionsDB.find_one({"id": queryId})
        if obj is not None or float(time.time() - start) > 30:
            break
        else:
            time.sleep(0.25)
    if obj is None:
        return Response(response="Bad Request - queryId not found in DB", headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    try:
        articles = obj['articles']
    except TypeError:
        return Response(response="Bad Request - object not contains articles",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)

    return articles, count, obj