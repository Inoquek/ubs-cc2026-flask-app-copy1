# routes/investigate.py
import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json

logger = logging.getLogger(__name__)


def calc1(data):
    ratios = data.get("ratios")
    goods = data.get("goods")

    n = len(goods)
    # connectivity_list = [[] for _ in range(n)]

    # for ratio in ratios:
    #     connectivity_list[ratio[0]].append([ratio[1], ratio[2]])


    dp = [[0 for _ in range(n)] for __ in range(n)]
    pr = [[0 for _ in range(n)] for __ in range(n)]

    for i in range(n):
        dp[i][i] = 1

    for _ in range(n):
        for source in range(n):
            for ratio in ratios:
                v = int(ratio[0])
                to = int(ratio[1])
                w = ratio[2]
                if dp[source][to] < (1.0 if source == v else dp[source][v]) * w:
                    dp[source][to] = dp[source][v] * w
                    pr[source][to] = v 

    logger.info(dp)
    logger.info(pr)
    mx = (dp[0][0], 0)
    for i in range(n):
        mx = max(mx, (dp[i][i], i))

    gain, start = mx
    v = pr[start][start]

    path = [goods[start], goods[v]]
    while v != start:
        v = pr[start][v]
        path.append(goods[v])

    path = path[::-1]

    return {"path": path, "gain": (gain - 1.0) * 100.0}
                

def calc2(data):
    ratios = data.get("ratios")
    goods = data.get("goods")


    n = len(goods)
    # connectivity_list = [[] for _ in range(n)]

    # for ratio in ratios:
    #     connectivity_list[ratio[0]].append([ratio[1], ratio[2]])


    dp = [[0 for _ in range(n)] for __ in range(n)]
    pr = [[0 for _ in range(n)] for __ in range(n)]

    for i in range(n):
        dp[i][i] = 1

    for _ in range(10):
        for source in range(n):
            for ratio in ratios:
                v = int(ratio[0])
                to = int(ratio[1])
                w = ratio[2]
                if dp[source][to] < (1.0 if source == v else dp[source][v]) * w:
                    dp[source][to] = dp[source][v] * w
                    pr[source][to] = v

    mx = (dp[0][0], 0)
    for i in range(n):
        mx = max(mx, (dp[i][i], i))

    gain, start = mx
    v = pr[start][start]

    path = [goods[start], goods[v]]
    while v != start:
        v = pr[start][v]
        path.append(goods[v])

    path = path[::-1]

    return {"path": path, "gain": gain * 100.0}
    # mx = (dp[0][0], 0, 0)
    # for i in range(n):
    #     for j in range(n):
    #         mx = max(mx, (dp[i][j], i, j))

    # gain, start, finish = mx
    # v = pr[start][finish]

    # path = [goods[finish], goods[v]]
    # while v != start:
    #     v = pr[start][v]
    #     path.append(goods[v])

    # path = path[::-1]

    # return {"path": path, "gain": gain * 100.0}


@app.route("/The-Ink-Archive", methods = ["POST"])
def ink_archieve():
    data = request.get_json()

    logging.info("data sent for evaluation {}".format(data))
    

    result = [calc1(data[0])]
    
    logging.info("investigate result: %s", data)
    return json.dumps(data)
