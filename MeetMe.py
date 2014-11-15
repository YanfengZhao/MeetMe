import webapp2
from google.appengine.ext import ndb

# Each app user's information
class AppUser(ndb.Model):
	userName = ndb.StringProperty()
	userID = ndb.StringProperty()
	blob_key = ndb.BlobKeyProperty()
	userFriends = ndb.StringProperty(repeated=True)
	userCurrentEvents = ndb.StringProperty(repeated=True)
	userPastEvents = ndb.StringProperty(repeated=True)
	userCreateDate = ndb.DateTimeProperty(auto_now_add=True)

	# User Inputs
	currentCity = ndb.StringProperty()
	occupation = ndb.StringProperty()
	age = ndb.StringProperty()

class Event(ndb.Model):
	user = ndb.StringProperty()
  	blob_key = ndb.BlobKeyProperty()
  	dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)
  	title = ndb.StringProperty(indexed=False)
  	destinationLoc = ndb.GeoPtProperty(required=True, default=ndb.GeoPt(0,0))
  	dateTimeToMeet = ndb.StringProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('This is Home Page')

class CreateEventSelectFriends(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('This is where you select your friends to join your event')

class CreateEventSelectLocation(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('This is where you select your event location')

class ViewYourEvents(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Here you can view your past and current events')

class Settings(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('You can set your settings here')

class ManageFriends(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('You can manage your friends here')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/createEventSelectFriends',CreateEventSelectFriends),
    ('/createEventSelectLocation',CreateEventSelectLocation),
    ('/viewYourEvents',ViewYourEvents),
    ('/settings',Settings),
    ('/manageFriends',ManageFriends)
], debug=True)