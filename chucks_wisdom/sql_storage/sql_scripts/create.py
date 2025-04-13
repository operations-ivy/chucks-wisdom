from __future__ import annotations

import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(
    conn,
    create_table_sql,
    create_id_value_idx_on_chuck_table,
    create_category_value_idx_on_chuck_table,
):
    """create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        c.execute(create_id_value_idx_on_chuck_table)
        c.execute(create_category_value_idx_on_chuck_table)
    except Error as e:
        print(e)


def main():
    database = "/home/zaphod/code/chucks-wisdom/chucks_wisdom/sql_storage/sqlite.db"

    sql_create_chuck_table = """ CREATE TABLE IF NOT EXISTS chuck (
                                        id text PRIMARY KEY,
                                        category text NOT NULL,
                                        value text NOT NULL,
                                        timestamp timestamp DEFAULT CURRENT_TIMESTAMP
                                    ); """

    sql_create_id_value_idx_on_chuck_table = (
        """ CREATE INDEX IF NOT EXISTS chuck_id_value_index ON chuck (id, value); """
    )
    sql_create_category_value_idx_on_chuck_table = (
        """ CREATE INDEX IF NOT EXISTS chuck_category_value_index ON chuck (category, value); """
    )
    conn = create_connection(database)

    if conn is not None:
        create_table(
            conn,
            sql_create_chuck_table,
            sql_create_id_value_idx_on_chuck_table,
            sql_create_category_value_idx_on_chuck_table,
        )
        #  alter_sql_id_idx,
        #  alter_sql_id_category_idx,
        #  alter_sql_id_category_value_idx)

    else:
        print("Error! cannot create the database connection.")


if __name__ == "__main__":
    main()
