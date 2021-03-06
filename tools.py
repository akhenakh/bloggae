#!/usr/bin/env python
# coding: utf-8
from functools import wraps
from datetime import datetime, timedelta, date
from google.appengine.api import users
from unicodedata import normalize


def _now():
    return datetime.now()


def abs_timedelta(delta):
    """Returns an "absolute" value for a timedelta, always representing a
    time distance."""
    if delta.days < 0:
        now = _now()
        return now - (now + delta)
    return delta


def date_and_delta(value):
    """Turn a value into a date and a timedelta which represents how long ago
    it was.  If that's not possible, return (None, value)."""
    now = _now()
    if isinstance(value, datetime):
        date = value
        delta = now - value
    elif isinstance(value, timedelta):
        date = now - value
        delta = value
    else:
        try:
            value = int(value)
            delta = timedelta(seconds=value)
            date = now - delta
        except (ValueError, TypeError):
            return (None, value)
    return date, abs_timedelta(delta)


def naturaldelta(value, months=True):
    """Given a timedelta or a number of seconds, return a natural
    representation of the amount of time elapsed.  This is similar to
    ``naturaltime``, but does not add tense to the result.  If ``months``
    is True, then a number of months (based on 30.5 days) will be used
    for fuzziness between years."""
    now = _now()
    date, delta = date_and_delta(value)
    if date is None:
        return value

    use_months = months

    seconds = abs(delta.seconds)
    days = abs(delta.days)
    years = days // 365
    days = days % 365
    months = int(days // 30.5)

    if not years and days < 1:
        if seconds == 0:
            return "a moment"
        elif seconds == 1:
            return "a second"
        elif seconds < 60:
            return "%d seconds" % (seconds)
        elif 60 <= seconds < 120:
            return "a minute"
        elif 120 <= seconds < 3600:
            return "%d minutes" % (seconds // 60)
        elif 3600 <= seconds < 3600*2:
            return "an hour"
        elif 3600 < seconds:
            return "%d hours" % (seconds // 3600)
    elif years == 0:
        if days == 1:
            return "a day"
        if not use_months:
            return "%d days" % days
        else:
            if not months:
                return "%d days" % days
            elif months == 1:
                return "a month"
            else:
                return "%d months" % months
    elif years == 1:
        if not months and not days:
            return "a year"
        elif not months:
            return "1 year, %d days" % days
        elif use_months:
            if months == 1:
                return "1 year, 1 month"
            else:
                return "1 year, %d months" % months
        else:
            return "1 year, %d days" % days
    else:
        return "%d years" % years


def admin_protect(f):
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        user = users.get_current_user()
        if not user or not users.is_current_user_admin():
            return self.redirect(users.create_login_url(self.request.uri))
        return f(self, *args, **kwargs)
    return decorated_function


def slugify(text, encoding=None,
         permitted_chars='abcdefghijklmnopqrstuvwxyz0123456789-'):
    if isinstance(text, str):
        text = text.decode(encoding or 'ascii')
    clean_text = text.strip().replace(' ', '-').lower()
    while '--' in clean_text:
        clean_text = clean_text.replace('--', '-')
    ascii_text = normalize('NFKD', clean_text).encode('ascii', 'ignore')
    strict_text = map(lambda x: x if x in permitted_chars else '', ascii_text)
    return ''.join(strict_text)
