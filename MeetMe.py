import webapp2
from google.appengine.ext import ndb
import json
from google.appengine.api import urlfetch
import urllib
import hashlib
import datetime

class Event(ndb.Model):
	user = ndb.StringProperty()
  	blob_key = ndb.BlobKeyProperty()
  	dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)
  	title = ndb.StringProperty(indexed=False)
  	dateTimeToMeet = ndb.StringProperty()
  	eventID = ndb.StringProperty()
  	activeEvent = ndb.StringProperty() # True or False
  	destinationLatitude = ndb.StringProperty()
  	destinationLongitude = ndb.StringProperty()
  	friendsEmails = ndb.StringProperty(repeated=True)
  	currentLocations = ndb.JsonProperty()
  	radius = ndb.StringProperty()
  	
# Each app user's information
class AppUser(ndb.Model):
	userName = ndb.StringProperty()
	userEmail = ndb.StringProperty() # user email
	userPassword = ndb.StringProperty() # user password
	blob_key = ndb.BlobKeyProperty() # profile image
	userFriends = ndb.StringProperty(repeated=True)
	userCurrentEvent = ndb.StringProperty()
	userPastEvents = ndb.StringProperty(repeated=True)
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
	
class CheckCurrentEventAvailability(webapp2.RequestHandler):
	def post(self):
		# check if the current user has current event
		currUserEmail = str(self.request.get("userEmail"))
		dictPassed = {}
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == currUserEmail:
				if user.userCurrentEvent == "None": 
					dictPassed = {"currentEventAvailable":"No"}
				else:
					dictPassed = {"currentEventAvailable":"Yes"}
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
					if user.userEmail == str(self.request.get("userEmail")).lower():
						if user.userPassword == hashlib.md5(str(self.request.get("userPwd"))).hexdigest():
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
					userEmail=str(self.request.get("userEmail")).lower(),
					userPassword=hashlib.md5(str(self.request.get("userPassword"))).hexdigest(),
					userName = str(self.request.get("userName")), 
					currentCity = str(self.request.get("currentCity")), 
					occupation = str(self.request.get("occupation")),
					age = str(self.request.get("age")),
					userCurrentEvent = "None"
				)
				appUser.put()
				q.globalUserEmails.append(str(self.request.get("userEmail")))
				q.put()

				dictPassed = {"signUpResult":"Signup Successful"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class RemoveUserHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"RemoveUserResult":"RemoveUserSuccessfully"}
		userToBeRemoved = str(self.request.get("userEmail"))
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == userToBeRemoved:
				user.key.delete()
		query = AllUsersEmails.query()
		for q in query:
			q.globalUserEmails.remove(userToBeRemoved)
			q.put()
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
				if str(self.request.get("friendEmail")) not in user.userFriends:
					user.userFriends.append(str(self.request.get("friendEmail")))
					user.put()
					dictPassed = {"addFriendResult":"Add Successful"}
				else:
					dictPassed = {"addFriendResult":"This Person Is Already Your Friend"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class CreateEventHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"CreateEventResult":"Event Create Successfully"}
		time = str(datetime.datetime.now()).replace(' ',".")
		event = Event(user = str(self.request.get("userEmail")),
			title = str(self.request.get("eventTitle")),
			dateTimeToMeet = str(self.request.get("dateTimeToMeet")),
			eventID = str(self.request.get("eventTitle"))+time,
			activeEvent = "True",
			destinationLongitude = str(self.request.get("destinationLongitude")),
			destinationLatitude = str(self.request.get("destinationLatitude")),
			radius = str(self.request.get("radius"))
			)
		event.put()

		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == str(self.request.get("userEmail")):
				user.userCurrentEvent = str(self.request.get("eventTitle"))+time
				user.put()
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class DeleteEventHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"DeleteEventResult":"Event Deleted Successfully"}
		eventToBeDeleted = str(self.request.get("eventID"))
		event_query = Event.query()
		user_query = AppUser.query()
		for event in event_query:
			if event.eventID == eventToBeDeleted:
				for user in user_query:
					if user.userEmail == event.user:
						if user.userCurrentEvent == event.eventID:
							user.userCurrentEvent = "None"
						if event.eventID in user.userPastEvents:
							user.userPastEvents.remove(event.eventID)
						user.put()
				for friendEmail in event.friendsEmails:
					for friend in user_query:
						if friend.userCurrentEvent == event.eventID:
							friend.userCurrentEvent = "None"
						if event.eventID in friend.userPastEvents:
							friend.userPastEvents.remove(event.eventID)
						friend.put()
				event.key.delete()
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class FinishEventHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"FinishEventResult":"Event Finished Successfully"}
		eventToBeFinished = str(self.request.get("eventID"))
		event_query = Event.query()
		user_query = AppUser.query()
		for event in event_query:
			if event.eventID == eventToBeFinished:
				event.activeEvent = "False"
				event.put()
				for friendEmail in event.friendsEmails:
					for friend in user_query:
						if friend.userEmail == friendEmail:
							friend.userCurrentEvent = "None"
							friend.userPastEvents.append(eventToBeFinished)
							friend.put()
				for user in user_query:
					if user.userEmail == event.user:
						user.userCurrentEvent = "None"
						user.userPastEvents.append(eventToBeFinished)
						user.put()
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class InviteFriendsHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {}
		eventID = str(self.request.get("eventID"))
		event_query = Event.query()
		user_query = AppUser.query()
		for friend in user_query:
			if friend.userEmail == str(self.request.get("friendEmail")):
				if friend.userCurrentEvent == "None":
					friend.userCurrentEvent = eventID
					friend.put()
					for event in event_query:
						if event.eventID == eventID:
							event.friendsEmails.append(str(self.request.get("friendEmail")))
							event.put()
					dictPassed = {"InviteResult":"Invite Successfully"}
				else:
					dictPassed = {"InviteResult":"Invite Failed. Friend is already in an event"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class UninviteFriendsHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"UninviteResult":"Uninvite Successfully"}
		eventID = str(self.request.get("eventID"))
		event_query = Event.query()
		user_query = AppUser.query()
		for friend in user_query:
			if friend.userEmail == str(self.request.get("friendEmail")):
				friend.userCurrentEvent = "None"
				friend.put()
		for event in event_query:
			if event.eventID == eventID:
				event.friendsEmails.remove(str(self.request.get("friendEmail")))
				event.put()
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

application = webapp2.WSGIApplication([
    ('/loginHandler',LoginHandler),
    ('/signUpHandler',SignUpHandler),
    ('/checkCurrentEventAvailability',CheckCurrentEventAvailability),
    ('/getUserFriendsHandler',GetUserFriendsHandler),
    ('/searchFriends',SearchFriends),
    ('/addFriendHandler',AddFriendHandler),
    ('/createEventHandler',CreateEventHandler),
    ('/deleteEventHandler',DeleteEventHandler),
    ('/removeUserHandler',RemoveUserHandler),
    ('/inviteFriendsHandler',InviteFriendsHandler),
    ('/uninviteFriendsHandler',UninviteFriendsHandler),
    ('/finishEventHandler',FinishEventHandler)
], debug=True)