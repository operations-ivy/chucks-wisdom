from __future__ import annotations

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
        html += "<h2>category: " + i[1] + "</br>"
        html += "<h3>value " + i[2]

    return html


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
