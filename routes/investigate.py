# routes/investigate.py
import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json

logger = logging.getLogger(__name__)

def calc(network):
    edges = network.get("network")
    connect_list = {}

    id = 0
    for edge in edges:
        user1 = edge.get("spy1")
        user2 = edge.get("spy2")
        if user1 not in connect_list:
            connect_list[user1] = []
        if user2 not in connect_list:
            connect_list[user2] = []
        connect_list[user1].append((user2, id))
        connect_list[user2].append((user1, id))
        id += 1

    ans = {"networkId": network.get("networkId"), "network": []}

    def dfs(visited, vertex, target, ban_id):
        if vertex == target:
            return True

        visited.add(vertex)
        for (to, id) in connect_list[vertex]:
            if to in visited or id == ban_id:
                continue

            if dfs(visited, to, target, ban_id) :
                return True
        
        return False
    
    id = 0
    for edge in edges:
        user1 = edge.get("spy1")
        user2 = edge.get("spy2")

        if dfs(set(), user1, user2, id):
            ans["network"].append({"spy1": user1, "spy2": user2})
        
        id += 1

    return ans


@app.route("/investigate", methods = ["POST"])
def investigate():
    data = request.get_json()

    logging.info("data sent for evaluation {}".format(data))
    
    networks = []
    is_list = False
    if isinstance(data, dict) :
        networks = data.get("networks")
    else:
        is_list = True
        networks = data

    # logging.info("Received networks: %d", len(networks))

    # if is_list:
    #     result = [calc(n) for n in networks]
    # else:
        # result = {"networks": [calc(n) for n in networks]}

    result = [calc(n) for n in networks]
    logging.info("investigate result: %s", result)
    return json.dumps(result)
