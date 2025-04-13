from __future__ import annotations

import datetime

import psycopg


class PGStorage:
    def __init__(self, db_connection_string):
        self.conn = psycopg.connect(db_connection_string)
        self.cursor = self.conn.cursor()

    def close_connection(self):
        self.cursor.close()
        self.conn.close()

    def insert_joke(self, joke_id, joke_category, joke_value):
        sql = """ INSERT INTO chuck(id,category,value,timestamp)
                VALUES(%(id)s,%(category)s,%(value)s,%(timestamp)s)
                ON CONFLICT (id)
                DO NOTHING"""
        self.cursor.execute(
            sql, {"id": joke_id, "category": joke_category, "value": joke_value, "timestamp": datetime.datetime.now()}
        )
        self.conn.commit()

    def check_for_duplicate(self, joke_id, joke_value):
        joke_exists = False
        sql = """ SELECT * FROM chuck WHERE id = %(id)s AND value = %(value)s """
        self.cursor.execute(sql, {"id": joke_id, "value": joke_value})
        if self.cursor.fetchone():
            joke_exists = True
        else:
            joke_exists = False

        return joke_exists

    def get_joke_id_by_value(self, joke_value):
        sql = """ SELECT id FROM chuck WHERE value = %(value)s """
        self.cursor.execute(sql, {"value": joke_value})
        return self.cursor.fetchone()

    def read_all_jokes(self):
        self.cursor.execute("SELECT * FROM chuck")

        return self.cursor.fetchall()
