from google.appengine.ext import ndb

class Post(ndb.Model):
    LIVE_STATUS = 1
    DRAFT_STATUS = 2
    HIDDEN_STATUS = 3
    STATUS_CHOICES = (
        (LIVE_STATUS, 'Live'),
        (DRAFT_STATUS, 'Draft'),
        (HIDDEN_STATUS, 'Hidden'),
        )

    title = ndb.StringProperty(required=True)
    tags = ndb.StringProperty(repeated=True)
    author = ndb.StringProperty(required=True)
    content_html = ndb.TextProperty(required=True)
    content_markup  = ndb.TextProperty()
    creation_date = ndb.DateTimeProperty(required=True, auto_now_add=True, indexed=False)
    modification_date = ndb.DateTimeProperty(required=True, auto_now_add=True, indexed=False)
    publication_date = ndb.DateTimeProperty(required=True, auto_now_add=True)
    status = ndb.IntegerProperty(default=DRAFT_STATUS, choices=[LIVE_STATUS, DRAFT_STATUS, HIDDEN_STATUS])
    is_bestof = ndb.BooleanProperty(default=False)
    markup = ndb.StringProperty(required=True, indexed=False)