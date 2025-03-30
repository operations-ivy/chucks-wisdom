from __future__ import annotations

import hashlib
import os

from flask import Flask

from chucks_wisdom.sqlite_storage.sqlite_storage import SqliteStorage


app = Flask(__name__)


@app.route("/")
def show_all_jokes():
    db_location = os.environ["DB_LOCATION"]
    storage = SqliteStorage(db_path=db_location)

    all_of_it = storage.read_all_jokes()

    html = ""
    for i in all_of_it:
        hashed_cat = hashlib.sha256(i[1].encode("utf-8")).hexdigest()
        hashed_val = hashlib.sha256(i[2].encode("utf-8")).hexdigest()
        html += "<tt>Category: " + hashed_cat + "</br>"
        html += "<tt>Value: " + hashed_val

    return html


@app.route("/health")
def health_check():
    return "OK"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
