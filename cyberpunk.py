from __future__ import annotations

import time

from flask import Flask, g, jsonify, render_template, request
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

import metrics
import reader
from tracing import init_tracing

init_tracing("chucks-wisdom-reader")
PsycopgInstrumentor().instrument()

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app, excluded_urls="health,metrics")


@app.before_request
def _start_timer():
    g.started = time.monotonic()


@app.after_request
def _count(response):
    # The matched route, not the raw path, so a scan for random paths can't
    # make new series.
    route = request.url_rule.rule if request.url_rule else "other"
    metrics.REQUESTS.labels(route, str(response.status_code)).inc()
    if "started" in g:
        metrics.REQUEST_SECONDS.labels(route).observe(time.monotonic() - g.started)
    return response


@app.route("/metrics")
def prometheus_metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


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
