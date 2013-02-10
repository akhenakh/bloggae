import json
import datetime
import re

class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.strftime('%Y-%m-%d %H:%M:%S')

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
def datetime_parser(entry):
    for k, v in entry.items():
        if isinstance(v, basestring) and re.search("^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$", v):
            try:
                entry[k] = datetime.datetime.strptime(v, DATE_FORMAT)
            except:
                pass
    return entry

data = json.loads(open("kdl.json").read(),  object_hook=datetime_parser)
posts = []
for entry in data:
    if entry['model'] == 'journal.comment':
        continue
    post = entry['fields']
    if post['tags'] == "":
        post['tags'] = []
    else:
        post['tags'] = post['tags'].split(" ")

    if post['user'] == 1:
        post['user'] = 'akh'
    else:
        post['user'] = 'toots'
    post['content_html'] = post['summary_html'] + post['content_html']
    post['content_markup'] = post['summary'] + post['content']
    post['url'] = post['creation_date'].strftime('/%Y/%m/%d/') + post['slug']
    print post['url']
    post['tags'] = [x for x in post['tags'] if x != '']

    posts.append(post)

open('posts.json',"w").write(json.dumps(posts, cls=MongoJsonEncoder))
