import webapp2
from google.appengine.ext import ndb
import json
import cgi
from google.appengine.api import urlfetch
import urllib


class Event(ndb.Model):
	user = ndb.StringProperty()
  	blob_key = ndb.BlobKeyProperty()
  	dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)
  	title = ndb.StringProperty(indexed=False)
  	destinationLoc = ndb.GeoPtProperty(required=True, default=ndb.GeoPt(0,0))
  	dateTimeToMeet = ndb.StringProperty()

# Each app user's information
class AppUser(ndb.Model):
	userName = ndb.StringProperty()
	userEmail = ndb.StringProperty() # user email
	userPassword = ndb.StringProperty() # user password
	blob_key = ndb.BlobKeyProperty() # profile image
	userFriends = ndb.StringProperty(repeated=True)
	userCurrentEvent = ndb.StructuredProperty(Event)
	userPastEvents = ndb.StructuredProperty(Event, repeated=True)
	userCreateDate = ndb.DateTimeProperty(auto_now_add=True)

	# User Inputs
	currentCity = ndb.StringProperty()
	occupation = ndb.StringProperty()
	age = ndb.StringProperty()

class AllUsersEmails(ndb.Model):
	globalUserEmails = ndb.StringProperty(repeated=True)

if AllUsersEmails.query().get() == None:
	allUsersEmails = AllUsersEmails()
	allUsersEmails.put()
	
class LoginPage(webapp2.RequestHandler):
    def get(self):
        dictPassed = {'pageName':"MainPage"}
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

class HomePage(webapp2.RequestHandler):
	def get(self):

		# check if the current user has current event
		currUserEmail = "kevzsolo@gmail.com"
		dictPassed = {}
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == currUserEmail:
				if user.userCurrentEvent is None or user.userCurrentEvent == "None": 
					dictPassed = {"currentEventAvailable":"No"}
				else:
					dictPassed = {"currentEventAvailable":"Yes"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class CreateEventSelectFriends(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('This is where you select your friends to join your event')
		dictPassed = {'pageName':"CreateEventSelectFriends"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class CreateEventSelectLocation(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('This is where you select your event location')
		dictPassed = {'pageName':"CreateEventSelectLocation"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class ViewYourEvents(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Here you can view your past and current events')

		#find current user
		user_query = AppUser.query()

		dictPassed = {'pageName':"ViewYourEvents"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class Settings(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('You can set your settings here')
		dictPassed = {'pageName':"Settings"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class ManageFriends(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('You can manage your friends here')
		dictPassed = {'pageName':"ManageFriends"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class LoginHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {}
		query = AllUsersEmails.query()
		for q in query:
			if str(self.request.get("userEmail")) not in q.globalUserEmails:
				dictPassed = {"loginResult":"User Email Does Not Exist"}
			else:
				user_query = AppUser.query()
				for user in user_query:
					if user.userEmail == str(self.request.get("userEmail")):
						if user.userPassword == str(self.request.get("userPwd")):
							dictPassed = {"loginResult":"Login Successful"}
						else:
							dictPassed = {"loginResult":"Invalid Password"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class SignUpHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {}
		# check if email address already exists
		query = AllUsersEmails.query()
		for q in query:
			if str(self.request.get("userEmail")) in q.globalUserEmails:
				dictPassed = {"signUpResult":"Duplicated Email Error"}
			else:
				appUser = AppUser(
					userEmail=str(self.request.get("userEmail")),
					userPassword=str(self.request.get("userPassword")),
					userName = str(self.request.get("userName")), 
					currentCity = str(self.request.get("currentCity")), 
					occupation = str(self.request.get("occupation")),
					age = str(self.request.get("age"))
				)
				appUser.put()
				q.globalUserEmails.append(str(self.request.get("userEmail")))
				q.put()

				dictPassed = {"signUpResult":"Signup Successful"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class GetUserFriendsHandler(webapp2.RequestHandler):
	def post(self):
		currUserEmail = str(self.request.get("userEmail"))
		friendList = []
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == currUserEmail:
				for friendEmail in user.userFriends:
					for user in user_query:
						if user.userEmail == friendEmail:
							tempDict = {"userName":user.userName, "userEmail":user.userEmail}
							friendList.append(tempDict)
		jsonObj = json.dumps(friendList, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class SearchFriends(webapp2.RequestHandler):
	def post(self):
		usersFound = []
		userInputString = self.request.get("searchContent")
		user_query = AppUser.query()
		for user in user_query:
			if userInputString in user.userName or userInputString in user.userEmail:
				tempDict = {"userName":user.userName,"userEmail":user.userEmail,"currentCity":user.currentCity, "age":user.age}
				usersFound.append(tempDict)
		jsonObj = json.dumps(usersFound, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class AddFriendHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"addFriendResult":"Add Failed"}
		currUserEmail = str(self.request.get("userEmail"))
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == currUserEmail:
				user.userFriends.append(str(self.request.get("friendEmail")))
				user.put()
				dictPassed = {"addFriendResult":"Add Successful"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)


application = webapp2.WSGIApplication([
    ('/', LoginPage),
    ('/createEventSelectFriends',CreateEventSelectFriends),
    ('/createEventSelectLocation',CreateEventSelectLocation),
    ('/viewYourEvents',ViewYourEvents),
    ('/settings',Settings),
    ('/manageFriends',ManageFriends),
    ('/loginHandler',LoginHandler),
    ('/signUpHandler',SignUpHandler),
    ('/homePage',HomePage),
    ('/getUserFriendsHandler',GetUserFriendsHandler),
    ('/searchFriends',SearchFriends),
    ('/addFriendHandler',AddFriendHandler)
], debug=True)