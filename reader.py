from __future__ import annotations

import hashlib
import os

from flask import Flask

from chucks_wisdom.sql_storage.pg_storage import PGStorage


app = Flask(__name__)


@app.route("/")
def show_all_jokes():
    db_connection_string = os.environ["DB_CONNECTION_STRING"]
    storage = PGStorage(db_connection_string)

    all_of_it = storage.read_all_jokes()

    html = ""
    for i in all_of_it:
        hashed_cat = hashlib.sha256(i[1].encode("utf-8")).hexdigest()
        hashed_val = hashlib.sha256(i[2].encode("utf-8")).hexdigest()
        html += f"""
            <pre>Category: {hashed_cat}
Value: {hashed_val}</pre>
        """

    return html


@app.route("/health")
def health_check():
    return "OK"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
