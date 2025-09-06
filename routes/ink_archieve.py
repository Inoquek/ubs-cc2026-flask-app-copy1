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
    connectivity_list = [[] for _ in range(n)]

    for ratio in ratios:
        connectivity_list[int(ratio[0])].append([int(ratio[1]), ratio[2]])

    
    num_mask = 2 ** n
    dp = [[[0.0 for _ in range(num_mask)] for ___ in range(n)] for __ in range(n)]
    pr = [[[1 for _ in range(num_mask)] for ___ in range(n)] for __ in range(n)]

    mx = (0, 0, 0)

    logger.info("Start!")

    for i in range(n):
        dp[i][i][2 ** i] = 1.0
        for mask in range(0, num_mask):
            if (mask & (2 ** i)) == 0:
                continue

            for prev_end in range(n):
                if (mask & (2 ** prev_end)) == 0:
                    continue
                for to_edge in connectivity_list[prev_end]:
                    to = to_edge[0]
                    w = to_edge[1]
                    if to == i:
                        continue
                    if (mask & (2 ** to)) == 0:
                        continue

                    nmask = (mask ^ int(2 ** to))
                    if dp[i][prev_end][nmask] * w > dp[i][to][mask]:
                        dp[i][to][mask] = dp[i][prev_end][nmask] * w
                        pr[i][to][mask] = prev_end

            for end in range(n):
                if not (mask & (2 ** end)):
                    continue
                else:
                    for to_edge in connectivity_list[end]:
                        if to_edge[0] == i:
                            if dp[i][end][mask] * to_edge[1] > mx[0]:
                                pr[i][i][mask] = end
                                mx = max(mx, (dp[i][end][mask] * to_edge[1], i, mask))


    logger.info("DP computed")
    gain, start, mask = mx
    v = pr[start][start][mask]
    path = [goods[start], goods[v]]

    logger.info([gain, start, mask, v])
    id = 0
    while v != start and id <= 10:
        new_mask = (mask ^ int(2 ** v))
        v = pr[start][v][mask]
        mask = new_mask
        path.append(goods[v])
        logger.info([new_mask, v])
        id += 1

    logger.info("Finished???")
    logger.info(path)
    path = path[::-1]

    return {"path": path, "gain": gain * 100.0}
                

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
                    dp[source][to] = (1.0 if source == v else dp[source][v]) * w
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
    

    result = [calc1(data[0]), calc1(data[1])]
    
    logging.info("investigate result: %s", data)
    return json.dumps(data)
