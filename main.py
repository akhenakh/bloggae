#!/usr/bin/env python

import os
import webapp2
from webapp2_extras import jinja2
from webapp2_extras.routes import RedirectRoute
#from google.appengine.ext import ndb
from models import Post
from migration import ImportHandler
import re
from tools import naturaldelta, admin_protect
import datetime
import StringIO
import PyRSS2Gen

post_re = re.compile(r'(\d{4})/(\d{2})/(\d{2})/([A-Za-z0-9-/]+)')


def jinja2_factory(app):
    j = jinja2.Jinja2(app)
    j.environment.filters.update({
        'naturaldelta':naturaldelta,
        })
    j.environment.globals.update({
        'Post': Post,
        #'ndb': ndb, # could be used for ndb.OR in templates
        })
    return j


class RSSHandler(webapp2.RequestHandler):
    def get(self):
        rss = PyRSS2Gen.RSS2(
            title=u'Keep Da Link',
            description=u'Updates for http://kdl.nobugware.com, Django, Python, Sun, Mac ...',
            link=u'http://kdl.nobugware.com',
            lastBuildDate = datetime.datetime.now(),
        )
        post_query = Post.query(Post.status==Post.LIVE_STATUS).order(-Post.publication_date)
        posts = post_query.fetch(10)
        items = []
        for post in posts:
            item = PyRSS2Gen.RSSItem(title=post.title,
                link="http://kdl.nobugware.com/post" + post.key.id(),
                description=post.content_html,
                pubDate=post.publication_date,
            )
            items.append(item)
        rss.items = items
        output = StringIO.StringIO()
        rss.write_xml(output, encoding='utf-8')
        self.response.write(output.getvalue())


class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(factory=jinja2_factory)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)


class HomeHandler(BaseHandler):
    def get(self):
        paging = 10
        try:
            page = int(self.request.get('page'))
        except ValueError:
            page = 0
        if page < 0:
            page = 0
        post_query = Post.query(Post.status==Post.LIVE_STATUS).order(-Post.publication_date)
        posts = post_query.fetch(paging, offset=page * paging)
        self.render_response("index.html", posts=posts, page=page)


class PostHandler(BaseHandler):
    def get(self, post_path):
        m = post_re.match(post_path)
        if not m:
            self.abort(404)
        year, month, day, slug = m.groups()
        if slug.endswith('/'):
            return self.redirect("/post/" + post_path[:-1])
        url = '/{year}/{month}/{day}/{slug}'.format(**locals())
        post = Post.get_by_id(url)

        if post is None:
            self.abort(404)
        self.render_response("post.html", post=post)


class AdminPostListHandler(BaseHandler):
    @admin_protect
    def get(self):
        paging = 20
        try:
            page = int(self.request.get('page'))
        except ValueError:
            page = 0
        if page < 0:
            page = 0
        post_query = Post.query(Post.status==Post.LIVE_STATUS).order(-Post.publication_date)
        posts = post_query.fetch(paging, offset=page * paging)
        self.render_response("admin.html", page=page, posts=posts)


class AdminPostEditHandler(BaseHandler):
    @admin_protect
    def get(self, post_path):
        m = post_re.match(post_path)
        if not m:
            self.abort(404)
        year, month, day, slug = m.groups()
        if slug.endswith('/'):
            return self.redirect("/post/" + post_path[:-1])
        url = '/{year}/{month}/{day}/{slug}'.format(**locals())
        post = Post.get_by_id(url)
        if post is None:
            self.abort(404)
        self.render_response("post_admin.html", post=post)


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([
    #('/upload', ImportHandler),
    RedirectRoute(r'/post/<:[A-Za-z0-9_\-\/]+>', PostHandler, name='post'),
    RedirectRoute(r'/feed/rss2', RSSHandler, name='rss', strict_slash=True),
    RedirectRoute('/admin', AdminPostListHandler, name='admin', strict_slash=True),
    RedirectRoute(r'/admin/post/<:[A-Za-z0-9_\-\/]+>', AdminPostEditHandler, name='postadmin'),
    RedirectRoute('/', HomeHandler, name='root', strict_slash=True),
], debug=debug)


