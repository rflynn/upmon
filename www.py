#!/usr/bin/env python2.7
# vim: set ts=4 et:

from flask import Flask, render_template, request, redirect, url_for

import sqlite3
import string
from datetime import date, datetime, timedelta
from urlparse import urlparse

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
    assert nth >= 0 and nth <= 100
    return sorted(l, key=key)[max(0,int(round((len(l) * (nth / 100.))))-1)]

@app.route('/')
def graph():

    now = datetime.now()
    six_hours_ago = now - timedelta(days=1)

    time_start = int(six_hours_ago.strftime('%s'))
    time_end = int(now.strftime('%s')) + 1
    url_id = 1

    c = dbx.cursor()
    c.execute('''
select
    scheme || '://' || netloc || path || '?' || query as urlstr
from url
where id=?
''',
    (url_id,))
    row = c.fetchone()
    print row
    url = urlparse(row['urlstr']).geturl() # normalize
    c.execute('''
select
    -- reqloc_id,
    -- http_request_id,
    time_start,
    duration_msec,
    http_code
    -- e.name,
    -- content_type_id,
    -- body_length,
    -- body_sha1_id
from result
join url on url.id = result.url_id
left join [except] e on e.id = result.except_id
where time_start between ? and ?
and url_id=?
order by result.id asc
''',
        (time_start,
         time_end,
         url_id))
    rows = list(c)
    c.close()

    availability = [[t, int(http_code >= 200 and http_code < 400) * 100]
                        for t, dur, http_code in rows]
    availability_pct = float(sum(up for _, up in availability)) / len(availability)

    resptime = [[t, dur]
                        for t, dur, http_code in rows]
    resptime_mean = float(sum(dur for _, dur in resptime)) / len(resptime)

    resptime_p98 = percentile(resptime, 98, key=lambda x: x[1])[1]

    except_ = [[t, int(http_code is None) * 100]
                        for t, dur, http_code in rows]
    except_pct = float(sum(x for _, x in except_)) / len(except_)

    current_date = datetime.now().strftime('%a, %b %d %Y %I:%M %p %Z')

    return render_template('graphs.html',
                           url=url,
                           current_date=current_date,
                           availability_pct=format_pct(availability_pct),
                           availability=availability,
                           resptime_mean=resptime_mean,
                           resptime=resptime,
                           resptime_p98=resptime_p98,
                           except_pct=format_pct(except_pct),
                           except_=except_)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',
            port=9999)
