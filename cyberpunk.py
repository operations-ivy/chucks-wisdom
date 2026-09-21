from __future__ import annotations

from flask import Flask, jsonify, render_template

import reader


app = Flask(__name__)


@app.route("/")
def console():
    return render_template("console.html")


@app.route("/api")
def api_entries():
    return jsonify(reader.read_hashed_entries())


@app.route("/health")
def health_check():
    return "OK"


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
