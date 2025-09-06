# routes/investigate.py
import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json

logger = logging.getLogger(__name__)


def calc(input):
    id = input.get("id")
    boats = input.get("input")

    events = []

    for boat in boats:
        start = boat[0]
        end = boat[1]

        events.append([start, 1])
        events.append([end + 1, -1])

    events = sorted(events)

    minBoatsNeeded = 0
    logger.info(boats)
    logger.info(events)
    cur = 0
    sortedMergedSlots = []
    L = -1
    for event in events:
        timestamp = event[0]
        type = event[1]
        if type == 1:
            cur += 1
            if cur == 1:
                L = timestamp
        else:
            cur -= 1
            if cur == 0:
                sortedMergedSlots.append([L, timestamp - 1])
        
        minBoatsNeeded = max(minBoatsNeeded, cur)

    ans = {"id": id, "sortedMergedSlots": sortedMergedSlots, "minBoatsNeeded": minBoatsNeeded}

    return ans


@app.route("/sailing-club/submission", methods = ["POST"])
def sailing_club():
    data = request.get_json()

    logging.info("data sent for evaluation {}".format(data))
    
    tests = data.get("testCases")

    result = {"solutions": [calc(t) for t in tests]}
    
    logging.info("investigate result: %s", result)
    return jsonify(result)
