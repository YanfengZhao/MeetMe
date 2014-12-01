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
  	dateTimeFinished = ndb.DateTimeProperty()
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
	longitude = ndb.StringProperty()
	latitude = ndb.StringProperty()

	# User Inputs
	currentCity = ndb.StringProperty()
	occupation = ndb.StringProperty()
	age = ndb.StringProperty()

class AllUsersEmails(ndb.Model):
	globalUserEmails = ndb.StringProperty(repeated=True)

if AllUsersEmails.query().get() == None:
	allUsersEmails = AllUsersEmails()
	allUsersEmails.put()

'''
Functionality: check if the user has a current event
Input: user's Email
Output: availability of event (Yes or No)
'''
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

'''
Functionality: log the user in
Input: 
	1. user's email
	2. user's password
Output: login Result (User Email Does Not Exist, Login Successful or Invalid Password)
'''
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

'''
Functionality: Sign up a new user
Input: 
	1. user's email
	2. user's password
	3. user's user name
	4. user's curre city
	5. user's occupation
	6. user's age
Output: sign up results (Duplicated Email Error or Signup Successful)
'''
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
					userCurrentEvent = "None",
					latitude = "0",
					longitude = "0"
				)
				appUser.put()
				q.globalUserEmails.append(str(self.request.get("userEmail")))
				q.put()

				dictPassed = {"signUpResult":"Signup Successful"}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

'''
Functionality: Remove a user from database
Input: user's email
Output: remove user result
'''
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

'''
Functionality: Get user's list of friends
Input: user's email
Output: list of friends
'''
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

'''
Functionality: search for new friends and display list of matching results
Input: search content
Output: list of people that match search content
'''
class SearchFriends(webapp2.RequestHandler):
	def post(self):
		usersFound = []
		userInputString = self.request.get("searchContent")
		user_query = AppUser.query()
		for user in user_query:
			if str(userInputString).lower() in str(user.userName).lower() or str(userInputString) in str(user.userEmail):
				tempDict = {
				"userName":user.userName,
				"userEmail":user.userEmail,
				"currentCity":user.currentCity, 
				"age":user.age
				}
				usersFound.append(tempDict)
		jsonObj = json.dumps(usersFound, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

'''
Functionality: add a new friend to user's friend list
Input:
	1. user's email
	2. friend's email
Output: add friend result(Add Failed, Add Successful, or This Person Is Already Your Friend)
'''
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

'''
Functionality: create a new event
Input: 
	1. event's title
	2. creator's email
	3. event's date and time of meeting
	4. destination longitude
	5. destination latitude
	6. geofence radius
Output: event's ID
'''
class CreateEventHandler(webapp2.RequestHandler):
	def post(self):
		time = str(datetime.datetime.now()).replace(' ',".")
		tempEventID = str(self.request.get("eventTitle"))+time
		dictPassed = {"eventID":tempEventID}
		event = Event(user = str(self.request.get("userEmail")),
			title = str(self.request.get("eventTitle")),
			dateTimeToMeet = str(self.request.get("dateTimeToMeet")),
			eventID = tempEventID,
			activeEvent = "True",
			destinationLongitude = str(self.request.get("destinationLongitude")),
			destinationLatitude = str(self.request.get("destinationLatitude")),
			radius = str(self.request.get("radius")),
			currentLocations = json.dumps([])
			)
		event.put()

		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == str(self.request.get("userEmail")):
				user.userCurrentEvent = str(self.request.get("eventTitle"))+time
				user.put()
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

'''
Functionality: delete an event
Input: event's ID
Output: delete event result
'''
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

'''
Functionality: complete an event, make a user's current event to None and move the event into user's past event list
Input: event's ID
Output: finish event result
'''
class FinishEventHandler(webapp2.RequestHandler):
	def post(self):
		dictPassed = {"FinishEventResult":"Event Finished Successfully"}
		eventToBeFinished = str(self.request.get("eventID"))
		event_query = Event.query()
		user_query = AppUser.query()
		for event in event_query:
			if event.eventID == eventToBeFinished:
				event.dateTimeFinished = datetime.datetime.now()
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

'''
Functionality: invite a friend to the event
Input:
	1. event's ID
	2. friend's email
Output: invite result (Invite Successfully or Invite Failed)
'''
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

'''
Functionality: uninvite a friend from an event
Input:
	1. event's ID
	2. friend's email
Output: uninvite result
'''
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

'''
Functionality: get the new location of a user and update it in datastore
Input:
	1. user's email
	2. user's longitude
	3. user's latitude
Output: None
'''
class UpdateGeoHandler(webapp2.RequestHandler):
	def post(self):
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == str(self.request.get("userEmail")):
				user.longitude = str(self.request.get("longitude"))
				user.latitude = str(self.request.get("latitude"))
				user.put()

'''
Functionality: for every active event, update the location of every user in the event in json property 
Input: None
Output: list of users and their locations updated 
'''
class CronHandler(webapp2.RequestHandler):
	def post(self):
		listOfLists = []
		event_query = Event.query()
		user_query = AppUser.query()
		for event in event_query:
			listOfDicts = []
			if event.activeEvent == "True":
				for friendEmail in event.friendsEmails:
					for friend in user_query:
						if friend.userEmail == friendEmail:
							tempDict = {
							"userEmail":friendEmail,
							"latitude":friend.latitude,
							"longitude":friend.longitude
							}
							listOfDicts.append(tempDict)
				for user in user_query:
					if event.user == user.userEmail:
						tempDict = {
						"userEmail":event.user,
						"latitude":user.latitude,
						"longitude":user.longitude
						}
						listOfDicts.append(tempDict)
			event.currentLocations = json.dumps(listOfDicts)
			event.put()
			listOfLists.append(listOfDicts)
		jsonObj = json.dumps(listOfLists, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

'''
Functionality: get user's current event information
Input: user's email
Output: user's current event information:
	1. geofence radius
	2. destination longitude
	3. destination latitude
	4. event's title
	5. event's ID
'''
class GetUserCurrentEventInformation(webapp2.RequestHandler):
	def post(self):
		dictPassed = {}
		userEmail = str(self.request.get("userEmail"))
		event_query = Event.query()
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == userEmail:
				for event in event_query:
					if user.userCurrentEvent == event.eventID:
						dictPassed = {
						"radius":event.radius,
						"destinationLongitude":event.destinationLongitude,
						"destinationLatitude":event.destinationLatitude,
						"title":event.title, 
						"eventID":event.eventID
						}

		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

'''
Functionality: get all users' current locations in an active event
Input: a user's email in an active event
Output: all user's location information in the same active event
'''
class GetUserCurrentLocation(webapp2.RequestHandler):
	def post(self):
		userEmail = str(self.request.get("userEmail"))
		event_query = Event.query()
		user_query = AppUser.query()
		for user in user_query:
			if user.userEmail == userEmail:
				for event in event_query:
					if user.userCurrentEvent == event.eventID:
						self.response.write(event.currentLocations)

'''
Functionality: return all the event a user has participated in
Input: user's email
Output: a list of user's past events and their information including
	1. event's title
	2. event's ID
	3. event's creator
	4. number of friends got invited to the event
	5. date and time the event was created
	6. date and time the event was finished
	7. meeting time
'''
class DisplayPastEventHandler(webapp2.RequestHandler):
	def post(self):
		userEmail = str(self.request.get("userEmail"))
		event_query = Event.query()
		user_query = AppUser.query()
		pastEvents = []
		for user in user_query:
			if user.userEmail == userEmail:
				for pastEvent in user.userPastEvents:
					for event in event_query:
						if pastEvent == event.eventID:
							tempDict = {
							"eventTitle":event.title,
							"eventID":event.eventID,
							"eventCreator":event.user,
							"numberOfFriendsInvited":str(len(event.friendsEmails)),
							"dateTimeCreated":str(event.dateTimeCreated),
							"dateTimeOfMeeting":str(event.dateTimeToMeet),
							"dateTimeFinished": str(event.dateTimeFinished)
							}
							pastEvents.append(tempDict)
		jsonObj = json.dumps(pastEvents, sort_keys=True,indent=4, separators=(',', ': '))
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
    ('/finishEventHandler',FinishEventHandler),
    ('/cronHandler',CronHandler),
    ('/updateGeoHandler',UpdateGeoHandler),
    ('/getUserCurrentEventInformation',GetUserCurrentEventInformation),
    ('/getUserCurrentLocation',GetUserCurrentLocation),
    ('/displayPastEventHandler',DisplayPastEventHandler)
], debug=True)