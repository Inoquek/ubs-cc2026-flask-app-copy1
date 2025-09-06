# routes/investigate.py
import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json
import numpy as np
logger = logging.getLogger(__name__)


# def calc1(data):
#     ratios = data.get("ratios")
#     goods = data.get("goods")

#     n = len(goods)
#     connectivity_list = np.array([[] for _ in range(n)])

#     for ratio in ratios:
#         connectivity_list[int(ratio[0])].append([int(ratio[1]), np.float64(ratio[2])])

    
#     num_mask = 2 ** n
#     dp = np.array([[[0.0 for _ in range(num_mask)] for ___ in range(n)] for __ in range(n)]).astype(np.float64)
#     pr = np.array([[[1 for _ in range(num_mask)] for ___ in range(n)] for __ in range(n)])

#     mx = (0, 0, 0)

#     logger.info("Start!")

#     for i in range(n):
#         dp[i][i][2 ** i] = 1.0
#         for mask in range(0, num_mask):
#             if (mask & int(2 ** i)) == 0:
#                 continue

#             for prev_end in range(n):
#                 if (mask & int(2 ** prev_end)) == 0:
#                     continue
#                 for to_edge in connectivity_list[prev_end]:
#                     to = to_edge[0]
#                     w = to_edge[1]
#                     if to == i:
#                         if dp[i][prev_end][mask] * to_edge[1] > dp[i][i][mask]:
#                             pr[i][i][mask] = prev_end
#                             dp[i][i][mask] = dp[i][prev_end][mask] * to_edge[1]
#                     if (mask & int(2 ** to)) == 0:
#                         continue

#                     nmask = (mask ^ int(2 ** to))
#                     if dp[i][prev_end][nmask] * w > dp[i][to][mask]:
#                         dp[i][to][mask] = dp[i][prev_end][nmask] * w
#                         pr[i][to][mask] = prev_end


#             if dp[i][i][mask] > mx[0]:
#                 mx = (dp[i][i][mask], i, mask)


#     logger.info("DP computed")
#     gain, start, mask = mx
#     v = pr[start][start][mask]
#     path = [goods[start], goods[v]]

#     logger.info([gain, start, mask, v])
#     while v != start:
#         new_mask = (mask ^ int(2 ** v))
#         logger.info(dp[start][v][mask])
#         v = pr[start][v][mask]
#         mask = new_mask
#         path.append(goods[v])
#         logger.info([new_mask, v])

#     logger.info("Finished???")
#     logger.info(path)
#     rev_path = path[::-1]

#     logger.info("Ready to Return")
#     return {"path": rev_path, "gain": float((gain - 1.0) * 100.0)}

def calc1(data):
    ratios = data.get("ratios")
    goods = data.get("goods")

    n = len(goods)
    # Use list of lists instead of numpy array for connectivity
    connectivity_list = [[] for _ in range(n)]

    for ratio in ratios:
        connectivity_list[int(ratio[0])].append([int(ratio[1]), np.float64(ratio[2])])

    num_mask = 2 ** n
    mx = 1.0
    path = [goods[0]]
    logger.info("Start!")

    for i in range(n):
        
        dp = np.zeros((n, num_mask), dtype=np.float64)
        pr = np.ones((n, num_mask), dtype=np.int32)
        dp[i, 2**i] = 1.0
        for mask in range(1, num_mask):
            if (mask & (2**i)) == 0:
                continue

            for prev_end in range(n):
                if (mask & (2**prev_end)) == 0:
                    continue
                    
                for to_edge in connectivity_list[prev_end]:
                    to = to_edge[0]
                    w = to_edge[1]
                    
                    if to == i:
                        # Path that ends at i
                        if dp[prev_end, mask] * w > dp[i, mask]:
                            pr[i, mask] = prev_end
                            dp[i, mask] = dp[prev_end, mask] * w
                    
                    # Skip if 'to' is not in the mask
                    if (mask & (2**to)) == 0:
                        continue
                        
                    # Remove 'to' from mask to get previous state
                    nmask = mask & ~(2**to)
                    if dp[prev_end, nmask] * w > dp[to, mask]:
                        dp[to, mask] = dp[prev_end, nmask] * w
                        pr[to, mask] = prev_end

            if dp[i, mask] > mx:
                start = i
                mx = dp[i, mask]
                v = pr[start, mask]
                path = [goods[start], goods[v]]
                
                logger.info([mx, start, mask, v])
                
                while v != start:
                    current_mask = mask
                    current = v
                    v = pr[current, current_mask]
                    # Only remove the current vertex after we've used it for lookup
                    mask = mask & ~(2**current)
                    path.append(goods[v])

    logger.info("DP computed")
    rev_path = path[::-1]

    logger.info("Ready to Return")
    return {"path": rev_path, "gain": float((mx - 1.0) * 100.0)}
                


@app.route("/The-Ink-Archive", methods = ["POST"])
def ink_archieve():
    data = request.get_json()

    logging.info("data sent for evaluation {}".format(data))
    

    result = [calc1(data[0]), calc1(data[1])]
    
    logging.info("investigate result: %s", result)
    return jsonify(result)
