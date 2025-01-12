from flask import Flask, jsonify
from blink_app.database import DBHandler

app = Flask(__name__)
db = DBHandler()

@app.route('/metrics', methods=['GET'])
def get_metrics():
    data = db.fetch_recent()
    return jsonify(data)
