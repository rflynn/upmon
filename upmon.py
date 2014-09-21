#!/usr/bin/env python2.7
# vim: set ts=4 noet:

from urlparse import urlparse
import requests
import time
from datetime import datetime
import hashlib
import sqlite3


def verify_ssl(): return False # LOL

def do_req(url, method=requests.post, headers=None, timeout=10, data=None, files=None, cookies=None, handler={}, debug=False):
    args = {
        'headers': headers if headers else {},
        'timeout': timeout,
        'verify': verify_ssl()
    }
    if data: args['data'] = data
    if files: args['files'] = files
    if cookies: args['cookies'] = cookies
    if debug: print 'args=%s' % args
    return method(url, **args)

def exception_to_str(e):
    return str(e.__class__)[8:-2].split('.')[-1]

assert exception_to_str(requests.exceptions.ConnectionError()) == 'ConnectionError'

db = {}

def get_dbconn(dbname='upmon.sqlite3'):
    global db
    if dbname in db:
        return db[dbname]
    db[dbname] = sqlite3.connect(dbname)
    db[dbname].row_factory = sqlite3.Row
    db[dbname].text_factory = str
    return db[dbname]

def save_url_results(reqloc,
                     http_request,
                     url,
                     time_start,
                     duration_msec,
                     http_code,
                     ex,
                     content_type,
                     body_length,
                     body_sha1):
    db = get_dbconn()
    c = db.cursor()

    c.execute('begin')

    c.execute(
'''
insert or ignore into url (
    scheme, netloc, path,
    query, fragment, username,
    password, hostname, port
) values (
    ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?
);
''',
        (url.scheme, url.netloc, url.path,
         url.query, url.fragment, url.username,
         url.password, url.hostname, url.port))

    c.execute('''insert or ignore into reqloc       (name) values (?);''', (reqloc,))
    c.execute('''insert or ignore into [except]     (name) values (?);''', (ex,))
    c.execute('''insert or ignore into content_type (name) values (?);''', (content_type,))
    c.execute('''insert or ignore into sha1         (name) values (?);''', (body_sha1,))
    c.execute('''
insert into result (
    reqloc_id,
    http_request_id,
    url_id,
    time_start,
    duration_msec,
    http_code,
    except_id,
    content_type_id,
    body_length,
    body_sha1_id
) values (
    1, -- reqloc_id,
    1, -- http_request_id,
    -- url_id,
    (select id from url where scheme=? and netloc=? and path=? and query=?),
    ?, -- time_start,
    ?, -- duration_msec,
    ?, -- http_code,
    (select id from [except] where name=?), -- except_id,
    (select id from content_type where name=?), -- content_type_id,
    ?, -- body_length,
    (select id from sha1 where name=?)  -- body_sha1_id
);
''', (
        # TODO: reqloc_id
        # TODO: http_request_id
        url.scheme, url.netloc, url.path, url.query,
        time_start,
        duration_msec,
        http_code,
        ex,
        content_type,
        body_length,
        body_sha1))
    db.commit()
    c.close()


def check_url(url, method=requests.get):
    reqloc = '127.0.0.1'
    http_request = ('GET', '')
    http_code = None
    ex = None
    header_date = None
    content_type = None
    body_length = None
    body_hash = None
    duration_msec = None
    body_sha1 = None
    time_start = time.time() # FIXME: need unix timestamp in UTC
    try:
        r = do_req(url.geturl(),
                   method=method)
        http_code = r.status_code
        content_type = r.headers.get('Content-Type')
        if content_type:
            content_type = content_type.lower()
        body_length = len(r.content) if r.content is not None else None
        body_sha1 = hashlib.sha1(r.content).digest()
        duration_msec = int(r.elapsed.microseconds / 1000)
    except Exception as e:
        print e
        ex = exception_to_str(e)
        duration_msec = int((time.time() - time_start) * 1000)
    save_url_results(reqloc,
                     http_request,
                     url,
                     int(time_start),
                     duration_msec,
                     http_code,
                     ex,
                     content_type,
                     body_length,
                     body_sha1)

if __name__ == '__main__':

    import sys
    if len(sys.argv) < 2:
        print 'usage: %s url' % (sys.argv[0],)
        sys.exit(1)
    check_url(urlparse(sys.argv[1]), requests.get)
    c = get_dbconn().cursor()   
    c.execute('select * from result order by id asc')
    for row in c:
        print dict(row)

