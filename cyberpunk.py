from __future__ import annotations

from flask import Flask, jsonify, render_template
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

import reader
from tracing import init_tracing

init_tracing("chucks-wisdom-reader")
PsycopgInstrumentor().instrument()

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


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
