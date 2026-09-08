import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

ROOT=Path(os.environ.get('EDITDNA_DATA', Path(__file__).resolve().parents[1]/'data')).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
for name in ('assets','audio','exports','demo'): (ROOT/name).mkdir(exist_ok=True)

def connect():
    c=sqlite3.connect(ROOT/'editdna.sqlite', timeout=30)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c

with connect() as c:
    old=c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records'").fetchone()
    if old and not any(r['name']=='kind' and r['pk'] for r in c.execute('PRAGMA table_info(records)')):
        c.execute('ALTER TABLE records RENAME TO records_legacy_v1')
        c.execute('CREATE TABLE records (id TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, PRIMARY KEY(kind,id))')
        c.execute('INSERT INTO records SELECT * FROM records_legacy_v1')
    c.execute('CREATE TABLE IF NOT EXISTS records (id TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL, created REAL NOT NULL, PRIMARY KEY(kind,id))')
    c.execute('CREATE INDEX IF NOT EXISTS records_kind ON records(kind)')

def new_id(): return uuid.uuid4().hex

def save(kind,body):
    body.setdefault('id',new_id())
    with connect() as c:
        c.execute('INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body',(body['id'],kind,json.dumps(body),time.time()))
    return body

def get(id,kind=None):
    with connect() as c:
        row=c.execute('SELECT * FROM records WHERE id=?'+(' AND kind=?' if kind else ''),(id,kind) if kind else (id,)).fetchone()
    if not row or (kind and row['kind']!=kind): raise KeyError(id)
    return json.loads(row['body'])

def all(kind):
    with connect() as c: rows=c.execute('SELECT body FROM records WHERE kind=? ORDER BY created DESC',(kind,)).fetchall()
    return [json.loads(r['body']) for r in rows]

def revise(kind,id,version,changes):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT body FROM records WHERE id=? AND kind=?',(id,kind)).fetchone()
        if not row: raise KeyError(id)
        body=json.loads(row['body'])
        if body.get('revision',1)!=version: raise ValueError('This item changed. Reload before saving.')
        body.update(changes); body['revision']=version+1
        c.execute('UPDATE records SET body=? WHERE id=? AND kind=?',(json.dumps(body),id,kind))
    return body
