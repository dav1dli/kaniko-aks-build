from flask import Flask, render_template
import os
from flask import jsonify

app = Flask(__name__)

FILE_SYSTEM_ROOT = "/mnt/data"

@app.route('/')
def hello_geek():
    return '<h1>Hello from Flask & Docker</h2>'


@app.route("/health")
def health():
    """health route"""
    state = {"status": "UP"}
    return jsonify(state)

@app.route('/data')
def browse():
    itemList = os.listdir(FILE_SYSTEM_ROOT)
    return render_template('browse.html', itemList=itemList)

if __name__ == "__main__":
    app.run(debug=True)
