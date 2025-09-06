import logging
from flask import request, jsonify
from routes import app


ATTACK_MINUTES = 10
COOLDOWN_MINUTES = 10

logger = logging.getLogger(__name__)

def solve_case(case):
    intel = case["intel"]
    reserve = case["reserve"]
    fronts = case["fronts"]
    stamina_max = case["stamina"]

    n = len(intel)
    dp = [-1 for _ in range(n + 1)]
    for idx in range(n):
        for j in range(0, idx + 1):
            time = 0
            mp = reserve
            stamina = stamina_max
            last_front = None
            for h in range(j + 2, idx + 1):
                if intel[h - 1][1] > mp or stamina == 0:
                    time += 10
                    mp = reserve
                    stamina = stamina_max
                    last_front = None
                
                mp -= intel[h - 1][1]
                stamina -= 1
                if not(last_front == intel[h - 1][0]):
                    time += 10
                last_front = intel[h - 1][0]

            if not(mp == reserve and stamina == stamina_max):
                time += 10
            dp[idx + 1] = dp[j] + time if dp[idx + 1] == -1 else min(dp[j] + time, dp[idx + 1])

    time = dp[n]
    return {"time": time}


@app.route("/the-mages-gambit", methods=["POST"])
def gambit():
    
    if not request.is_json:
        return jsonify({"error": "Expected application/json body"}), 400
    payload = request.get_json()
    
    # assert len(payload) == 10
    
    # for case in [2, 5, 10]:
    #     logger.info(f"Case {case}:")
    #     logger.info(payload[case-1])

    logger.info(payload)
    if not isinstance(payload, list):
        return jsonify({"error": "Expected a JSON array of cases"}), 400
    
    
    # try:
    result = [solve_case(case) for case in payload]
    # except (KeyError, TypeError, ValueError) as e:
    #     return jsonify({"error": str(e)}), 400

    return jsonify(result), 200