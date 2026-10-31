from __future__ import annotations

import brick_observe
from flask import Flask, jsonify, render_template
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

import reader

brick_observe.init("chucks-wisdom-reader")
PsycopgInstrumentor().instrument()

app = Flask(__name__)
brick_observe.flask.instrument(app)


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
