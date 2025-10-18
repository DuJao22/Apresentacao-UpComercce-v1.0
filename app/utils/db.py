import sqlite3
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except sqlite3.Error as e:
            logger.error(f"Erro ao fechar conexão do banco de dados: {e}")

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar query: {query}, Erro: {e}")
        return None if one else []

def execute_db(query, args=()):
    try:
        db = get_db()
        cursor = db.execute(query, args)
        db.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar comando: {query}, Erro: {e}")
        db = get_db()
        db.rollback()
        raise
