import json
import re
import datetime
import webapp2
from models import Post

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def datetime_parser(entry):
    for k, v in entry.items():
        if isinstance(v, basestring) and re.search("^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$", v):
            try:
                entry[k] = datetime.datetime.strptime(v, DATE_FORMAT)
            except:
                pass
    return entry


class ImportHandler(webapp2.RequestHandler):
    def post(self):
        data = self.request.get('data')
        new_data = json.loads(data, object_hook=datetime_parser)
        for post in new_data:
            #logging.info(post)

            post_obj = Post(id=post['url'],
                title = post['title'],
                tags = post['tags'],
                author = post['user'],
                markup = post['markup'],
                is_bestof = post['is_bestof'],
                status = post['status'],
                content_html = post['content_html'],
                content_markup = post['content_markup'],
                creation_date = post['creation_date'],
                publication_date = post['publication_date'],
                modification_date = post['modification_date']
            )
            post_obj.put()
