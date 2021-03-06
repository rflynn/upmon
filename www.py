#!/usr/bin/env python2.7
# vim: set ts=4 et:

from flask import Flask, render_template, request, redirect, url_for

import sqlite3
import string
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
import urllib

# flask app core
app = Flask(__name__, static_url_path='')

# strip whitespace after template rendering
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# database connection
dbx = sqlite3.connect('./upmon.sqlite3', check_same_thread=False)
dbx.isolation_level = 'DEFERRED'
dbx.row_factory = sqlite3.Row

def format_pct(pct):
    if pct == 0 or pct == 100:
        return int(pct)
    return round(pct, 4)

def percentile(l, nth, key=lambda x: x):
    if not l:
        return None
    assert 0 <= nth <= 100
    p_relative = len(l) * (nth / 100.)
    p_round = int(round(p_relative))
    p_index = max(0, p_round - 1)
    return sorted(l, key=key)[p_index]

# given a possibly urlencoded url, decode it, normalize it, look it up in our db
def get_url_id(url_enc):
    url_str = urllib.unquote(url_enc).decode('utf8')
    u = urlparse(url_str)

    c = dbx.cursor()
    c.execute('select id from url where scheme=? and netloc=? and path=? and query=?',
        (u.scheme, u.netloc, u.path, u.query,))
    row = c.fetchone()
    c.close()

    url_id = row[0] if row else None
    url = u.geturl() # normalize
    return url_id, u.geturl()

def url_data(url_id, now, start):
    time_start = int(start.strftime('%s'))
    time_end = int(now.strftime('%s')) + 1
    c = dbx.cursor()
    c.execute('''
select
    time_start,
    duration_msec,
    http_code
from result
join url on url.id = result.url_id
where url_id=?
and time_start between ? and ?
order by result.id asc
''',
        (url_id,
         time_start,
         time_end))
    rows = list(c)
    c.close()
    return rows

def url_data_aggregate(url_id, now, start, period_sec):
    time_start = int(start.strftime('%s'))
    time_end = int(now.strftime('%s')) + 1
    #print (url_id, time_start, time_end, period_sec)
    c = dbx.cursor()
    c.execute('''
select
    min(time_start),
    cast((avg(duration_msec)) as int),
    max(http_code)
from result
join url on url.id = result.url_id
where url_id=?
and time_start between ? and ?
group by time_start - (time_start % ?)
order by result.id asc
''',
        (url_id,
         time_start,
         time_end,
         period_sec * 60))
    rows = [list(row) for row in c]
    c.close()
    return rows

@app.route('/')
def root():
    return graph(request.url) # graph self

@app.route('/u/<path:url_enc>')
def graph(url_enc):

    url_id, url = get_url_id(url_enc)
    if url_id is None:
        return # TODO: render error message

    now = datetime.now()
    day = url_data(url_id, now, now - timedelta(days=1))
    week = url_data_aggregate(url_id, now, now - relativedelta(weeks=1), 60) # every hour for a week
    month = url_data_aggregate(url_id, now, now - relativedelta(months=6), 60*4) # every 4 hours for a month

    availability = [[t, int(http_code >= 200 and http_code < 400) * 100]
                        for t, dur, http_code in day]
    availability_pct = float(sum(up for _, up in availability)) / max(1, len(availability))

    resptime = [[t, dur]
                        for t, dur, http_code in day]
    resptime_mean = float(sum(dur for _, dur in resptime)) / max(1, len(resptime))

    p = percentile(resptime, 98, key=lambda x: x[1])
    resptime_p98 = p[1] if p else 0.0

    except_ = [[t, int(http_code is None) * 100]
                        for t, dur, http_code in day]
    except_pct = float(sum(x for _, x in except_)) / max(1, len(except_))

    current_date = datetime.now().strftime('%a, %b %d %Y %I:%M %p %Z')

    return render_template('graphs.html',
                           url=url,
                           current_date=current_date,
                           availability_pct=format_pct(availability_pct),
                           availability=availability,
                           day=[list(d) for d in day],
                           week=week,
                           resptime_mean=resptime_mean,
                           resptime=resptime,
                           resptime_p98=resptime_p98,
                           except_pct=format_pct(except_pct),
                           except_=except_)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',
            port=9999)
