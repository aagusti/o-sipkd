#!/usr/bin/python

import sys
from config import (db_url_dst)
from tools import humanize_time, print_log, eng_profile, stop_daemon
import os
import demon
import signal
import csv
import os
import io
from time import time
from sqlalchemy import create_engine, func
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import DatabaseError
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Sequence, SmallInteger, BigInteger
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship
    )
    
from datetime import datetime
from urllib import unquote_plus
from urlparse import urlparse
from optparse import OptionParser
from datetime import date

def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))

    return d        
    
def info(s):
    print_log(s)
    log.info(s)
    
def error(s):
    print_log(s,'ERROR')
    log.error(s)    
SQL_TABLE = """
SELECT c.oid, n.nspname, c.relname
  FROM pg_catalog.pg_class c
  LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relname = :table_name
    AND pg_catalog.pg_table_is_visible(c.oid)
  ORDER BY 2, 3
"""

SQL_TABLE_SCHEMA = """
SELECT c.oid, n.nspname, c.relname
  FROM pg_catalog.pg_class c
  LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relname = :table_name
    AND n.nspname = :schema
  ORDER BY 2, 3
"""

SQL_FIELDS = """
SELECT a.attname,
  pg_catalog.format_type(a.atttypid, a.atttypmod),
  (SELECT substring(pg_catalog.pg_get_expr(d.adbin, d.adrelid) for 128)
     FROM pg_catalog.pg_attrdef d
     WHERE d.adrelid = a.attrelid
       AND d.adnum = a.attnum
       AND a.atthasdef) AS substring,
  a.attnotnull, a.attnum,
  (SELECT c.collname
     FROM pg_catalog.pg_collation c, pg_catalog.pg_type t
     WHERE c.oid = a.attcollation
       AND t.oid = a.atttypid
       AND a.attcollation <> t.typcollation) AS attcollation,
  NULL AS indexdef,
  NULL AS attfdwoptions
  FROM pg_catalog.pg_attribute a
  WHERE a.attrelid = :table_id AND a.attnum > 0 AND NOT a.attisdropped
  ORDER BY a.attnum"""

eng_dst = create_engine(db_url_dst)
DBSession = scoped_session(sessionmaker())
Base = declarative_base()
DBSession.configure(bind=eng_dst)
Base.metadata.bind = eng_dst
#eng_dst.echo =True
class base(object):
    def to_dict(self): # Elixir like
        values = {}
        for column in self.__table__.columns:
            values[column.name] = getattr(self, column.name)
        return values
        
    def from_dict(self, values):
        for column in self.__table__.columns:
            if column.name in values:
                setattr(self, column.name, values[column.name])

    def as_timezone(self, fieldname):
        date_ = getattr(self, fieldname)
        return date_ and as_timezone(date_) or None
        
    @classmethod
    def get_id_by_kode(cls, kode):
          return DBSession.query(cls.id).filter(cls.kode==kode)
          
def table_seq(table):
    engine = DBSession.bind
    if table.schema:
        sql = text(SQL_TABLE_SCHEMA)
        q = engine.execute(sql, schema=table.schema, table_name=table.name)
    else:
        sql = text(SQL_TABLE)
        q = engine.execute(sql, table_name=table.name)    
    r = q.fetchone()
    table_id = r.oid
    sql = text(SQL_FIELDS)
    q = engine.execute(sql, table_id=table_id)
    regex = re.compile("nextval\('(.*)'\:")
    for r in q.fetchall():
        if not r.substring:
            continue
        if r.substring.find('nextval') == -1:
            continue
        match = regex.search(r.substring)
        return match.group(1)
        
def set_sequence(orm):
    seq_name = table_seq(orm.__table__)
    if not seq_name:
        return
    row = DBSession.query(orm).order_by('id DESC').first()
    last_id = row and row.id or 1
    sql = "SELECT setval('%s', %d)" % (seq_name, last_id)
    engine = DBSession.bind
    engine.execute(sql)