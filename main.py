#!/usr/bin/env python
# coding: utf-8

import os
import webapp2
from webapp2_extras import jinja2
from webapp2_extras.routes import RedirectRoute
#from google.appengine.ext import ndb
from models import Post
from migration import ImportHandler
import re
from tools import naturaldelta, admin_protect, slugify
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

    def gen_id(self, post_path):
        """ generate id from the path """
        m = post_re.match(post_path)
        if not m:
            self.abort(404)
        year, month, day, slug = m.groups()
        return '/{year}/{month}/{day}/{slug}'.format(**locals())


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
        post_query = Post.query().order(-Post.publication_date)
        posts = post_query.fetch(paging, offset=page * paging)
        self.render_response("admin.html", page=page, posts=posts)


class AdminPostDeleteHandler(BaseHandler):
    @admin_protect
    def post(self, post_path):
        url = self.gen_id(post_path)
        post = Post.get_by_id(url)
        post.key.delete()
        return self.redirect("/admin")


class AdminPostHandler(BaseHandler):
    def temp_post(self, post_obj=None):
        # we need this fake populated Post cause the id is built with creation_date and title
        post = post_obj
        if post is None:
            post = Post()
        try:
            status = int(self.request.get('status', default_value=Post.DRAFT_STATUS))
        except (ValueError, TypeError):
            status = Post.DRAFT_STATUS
        tags = [tag.strip() for tag in self.request.get('tags').split(',')]
        if tags[0] == '':
            tags = []
        if not post.markup:
            post.markup = 'html'
        now = datetime.datetime.utcnow()
        post.populate(creation_date=now if not post.creation_date else post.creation_date,
                      publication_date=now if not post.publication_date else post.publication_date,
                      modification_date=now if not post.modification_date else post.modification_date,
                      author='akh',
                      title=self.request.get('title', default_value=""),
                      tags=tags,
                      status=status,
                      is_bestof=True if self.request.get('is_bestof') else False,
                      content_html=self.request.get('content_html', default_value=""))
        return post

    @admin_protect
    def get(self, post_path=None):
        if post_path is not None:
            url = self.gen_id(post_path)
            post = Post.get_by_id(url)
            if post is None:
                self.abort(404)

        else:
            post = self.temp_post()
        self.render_response("post_admin.html", post=post)

    @admin_protect
    def post(self, post_path=None):
        if post_path is not None:
            url = self.gen_id(post_path)
            post = Post.get_by_id(url)
            post = self.temp_post(post_obj=post)
        else:
            today = datetime.datetime.utcnow()
            date = today.strftime("%Y/%m/%d")
            # if we have a title we can create a slug then really save the post
            slug = slugify(self.request.get('title'))
            if slug:
                new_id = '/{date}/{slug}'.format(**locals())
                post = Post(id=new_id)
                post = self.temp_post(post_obj=post)
            else:
                post = self.temp_post()
        post.modification_date = datetime.datetime.utcnow()
        if post.key is not None:
            post.put()
        self.render_response("post_admin.html", post=post)

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([
    #('/upload', ImportHandler),
    RedirectRoute(r'/post/<:[A-Za-z0-9_\-\/]+>', PostHandler, name='post'),
    RedirectRoute(r'/feed/rss2', RSSHandler, name='rss', strict_slash=True),
    RedirectRoute('/admin', AdminPostListHandler, name='admin', strict_slash=True),
    RedirectRoute('/admin/post/new', AdminPostHandler, name='postnewadmin', strict_slash=True),
    RedirectRoute('/admin/post/delete/<:[A-Za-z0-9_\-\/]+>', AdminPostDeleteHandler, name='postdeleteadmin', strict_slash=True),
    RedirectRoute(r'/admin/post/<:[A-Za-z0-9_\-\/]+>', AdminPostHandler, name='postadmin'),
    RedirectRoute('/', HomeHandler, name='root', strict_slash=True),
], debug=debug)


