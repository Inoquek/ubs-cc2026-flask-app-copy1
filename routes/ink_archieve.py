# routes/investigate.py
import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json

logger = logging.getLogger(__name__)




@app.route("/The-Ink-Archive", methods = ["POST"])
def ink_archieve():
    data = request.get_json()

    logging.info("data sent for evaluation {}".format(data))
    
    
    logging.info("investigate result: %s", data)
    return json.dumps(data)
