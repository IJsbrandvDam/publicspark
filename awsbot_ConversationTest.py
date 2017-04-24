from itty import *
import json
from ciscosparkapi import CiscoSparkAPI
import requests
import sys
import os
from generateResponse import generateResponse
from DBconnect import sendToDatabase, pullFromDatabase, createDatabase, deleteDatabase

threadList = []


#used to track conversation process
class activeThread():
    def __init__(self, roomID, userID, conValue = 0, repeatCounter = 0):
        self.roomID = roomID
        self.userID = userID
        self.conValue = conValue
        self.repeatCounter = repeatCounter
        
    def setConversationValue(self, i):
        self.conValue = i

    def getConversationValue(self):
        return(self.conValue)

    def getRoomID(self):
        return(self.roomID)

    def setRepeatCounter(self, i):
        self.repeatCounter = i

    def getRepeatCounter(self):
        return(self.repeatCounter)

    def getUserID(self):
        return(self.userID)

#check if a room already has a thread:
def GetThreadIndex(messageRoom):
    hasActive = False
    index = -1
    activeIndex = None

    for objects in threadList:
        index = index + 1
        if objects.getRoomID() == messageRoom:
            hasActive = True
            activeIndex = index

    return activeIndex

#call after message is "start" has been reveived to start a new conversation thread
def CreateActiveThread(roomID, userID, messageText):
    i = GetThreadIndex(roomID)
    if i == None:
        #print("no active thread found, created thread for room " + str(roomID))
        threadList.append(activeThread(roomID, userID))
        i = GetThreadIndex(roomID)
        NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID)
        #print("created conversation")
    else:
        #print("thread already active, so using it as an input instead")
        NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID)

#call after every received message to check if the room is currently involved in a conversation thread
def CheckActiveThread(roomID, userID, messageText):
    i = GetThreadIndex(roomID)
    if i == None:
        print("no active thread found for room " + str(roomID))

    else:
        string1 = str(userID)
        string2 = threadList[i].getUserID()
        if string1 == string2:
            #print("user matches")
            NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID)
        else:
            SendMessage("Someone else already initiated a session in this room, please let them finish the initialization before starting a new one", roomID)

#delete conversation thread for roomID with index <index>
def DeleteActiveThread(index):
    if index == None:
        print("unable to delete active thread for " + str(roomID) + " because no thread exists")
    else:
        del threadList[index]
        print("deleted thread for roomID " + str(roomID))

#Used to determine the flow of conversation
def NextStepInConversation(conversationState, index, t, roomID):
    #print("next step called")
    messageText = str(t)

    if(conversationState == 0):
        SendMessage(SetConversationResponseText(0), roomID)
        threadList[index].setConversationValue(1)

    elif(conversationState == 1):
        if(messageText.lower() == "blank session"):
            SendMessage(SetConversationResponseText(1), roomID)
            threadList[index].setConversationValue(2)

        elif(messageText.lower() == "template"):
            SendMessage(SetConversationResponseText(7), roomID)
            threadList[index].setConversationValue(6)

        else:
            SendMessage("Sorry I do not recognize that input, please select either blank session or template", roomID)

    elif(conversationState == 2):
        threadList[index].setRepeatCounter(int(messageText)-1)
        text = SetConversationResponseText(2) + str(threadList[index].getRepeatCounter())
        SendMessage(text, roomID)
        threadList[index].setConversationValue(3)


    elif(conversationState == 3):
        if threadList[index].getRepeatCounter() > 0 :
            SendMessage(SetConversationResponseText(2), roomID)
            threadList[index].setRepeatCounter(threadList[index].getRepeatCounter()-1)

        else:
            SendMessage(SetConversationResponseText(3), roomID)
            threadList[index].setConversationValue(4)

    elif(conversationState == 4):
        if(messageText.lower() == "no"):
            SendMessage(SetConversationResponseText(4), roomID)
            DeleteActiveThread(index)
            StartSession()

        elif(messageText.lower() == "yes"):
            SendMessage(SetConversationResponseText(5), roomID)
            threadList[index].setConversationValue(5)

    elif(conversationState == 5):
        if(MatchTemplate(messageText)):
            StoreTemplate(messageText)
            SendMessage(SetConversationResponseText(6), roomID)
            DeleteActiveThread(index)
            StartSession()
        else:
            SendMessage(SetConversationResponseText(10), roomID)

    elif(conversationState == 6):
        if(messageText.lower() == "new template"):
            SendMessage(SetConversationResponseText(1), roomID)
            threadList[index].setConversationValue(2)

        else:
            SendMessage(SetConversationResponseText(8), roomID)
            LoadTemplate(messageText)
            threadList[index].setConversationValue(7)

    elif(conversationState == 7):
        if(messageText.lower() == "no"):
            SendMessage(SetConversationResponseText(9), roomID)
            DeleteActiveThread(index)

        elif(messageText.lower() == "yes"):
            SendMessage(SetConversationResponseText(4), roomID)
            DeleteActiveThread(index)
            StartSession()


#used to set the basic text for the next response
def SetConversationResponseText(conversationValue):
    if(conversationValue == 0):
        return("Would you like to start a blank session or load a template?")

    elif(conversationValue == 1):
        return("How many questions would you like to include?")

    elif(conversationValue == 2):
        return("Please type question ")

    elif(conversationValue == 3):
        return("Would you like to save this BrainSpark session as a template?")

    elif(conversationValue == 4):
        return("OK! Let's start!")

    elif(conversationValue == 5):
        return("What name would you like to use for the template?")

    elif(conversationValue == 6):
        return("OK! The template has been saved. Let's start!")

    elif(conversationValue == 7):
        return("Which template would you like to use?")

    elif(conversationValue == 8):
        return("Would you like to start a session with this template? It contains the following questions: ")

    elif(conversationValue == 9):
        return("No problem! Let me know when you want to start a new session.")

    elif(conversationValue == 10):
        return("I'm sorry, there is no template with that name, please try again")

#placeholder for sending message
def SendMessage(text, room_id):
    spark.messages.create(roomId=room_id, text=text)

#placeholder for starting BrainSpark session
def StartSession():
    #SendMessage("starting session...")

#placeholder for storing the template
def StoreTemplate(name):
    #SendMessage("stored template with name " + name)

#placeholder for listing the templates
def ListTemplates():
    #SendMessage("placeholder for the template list")

#placeholder for loading a template
def LoadTemplate(name):
    #SendMessage("template " + name + "has been loaded. It contains the following questions: <list will follow>")

#placeholder for checking if template exists
def MatchTemplate(name):
    #SendMessage("template found")
    #return(True)

@post('/')
def index(request):
    spark = CiscoSparkAPI(access_token=bearer) # spark apis
    webhook = json.loads(request.body) # get payload from webhook
    room_id = webhook['data']['roomId'] # get room id from message
    message_id = webhook['data']['id'] # get message id
    message = spark.messages.get(message_id) # retrieve message using message id
    room_name = spark.rooms.get(room_id) # retrieve room information to get the room name
    personName = spark.people.list()

    # Code for the bot to speak. First we make sure that it only responds to messages NOT from the bot itself
    if webhook['data']['personEmail'] != bot_email:
        # parse the initiation message to remove the bot tag
        in_message = message.text.replace(bot_name, '')
        # conditional for the initiation of the test. 
        # here we filter for a message from a "group" room and for the message "start"
        # If it matches then send a message to the group room, and also send a message to each person individually
        if message.roomType == "group" and 'start' in in_message:
            memberList = spark.memberships.list(roomId=room_id)
            GROUP_MESSAGE = "Brainstorming session for '%s' is starting." % (room_name.title)
            spark.messages.create(roomId=room_id, text=GROUP_MESSAGE) # Message the room.
            for Membership in memberList: # Message each member in the room individually.
                if Membership.personEmail != bot_email and Membership.personEmail != security_email: # filter out the bot and cisco security bot, we dont want to send them a message!
                    INTRO_MESSAGE = "You have been invited to brainstorming session '%s'. Type 'help' for a brief introduction on how I work! What is your idea?" % (room_name.title)
                    spark.messages.create(toPersonEmail=Membership.personEmail, text=INTRO_MESSAGE)
                    createDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
                    #TODO: Save list of people involved in this brainstorm & group roomId.
                    # Likely another database. This one is roomId, memberList.
        # conditional to end the test
        # same idea as above but then for the word end
        # should also post the final idea into the group room
        elif message.roomType == "group" and "end" in in_message:
            memberList = spark.memberships.list(roomId=room_id)
            GROUP_MESSAGE = "Brainstorming session for '%s' is ending." % (room_name.title)
            spark.messages.create(roomId=room_id, text=GROUP_MESSAGE) # Message the room.
            for Membership in memberList: # Message each member in the room individually.
                if Membership.personEmail != bot_email and Membership.personEmail != security_email:
                    END_MESSAGE = "Brainstorming session '%s' is ending." % (room_name.title)
                    spark.messages.create(toPersonEmail=Membership.personEmail, text=END_MESSAGE)
                    deleteDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
            #TODO: Send the best idea to the group chat.
            BEST_IDEA = "The best idea." #getBestIdea(room_id)
            spark.messages.create(roomId=room_id, text=BEST_IDEA)
       #placeholder to test conversation, convert to 'start' when working
        elif message.roomType == "group" and 'begin' in in_message:
            CreateActiveThread(room_id, message.personEmail, in_message) 

        elif message.roomType == "group":
            CheckActiveThread(room_id, message.personEmail, in_message)

 # looks for personal messages in 1:1 conversations. These messages need to be saved to our database
        else:

            if message.roomType == "direct":
                if in_message == "help":
                    spark.messages.create(toPersonEmail=message.personEmail, text="explanation of how this works, what is your idea")
                    return "true"
                #Temp making sure it tries to do this:
                spark.messages.create(toPersonEmail=message.personEmail, text="processing...")
                # TODO: Save message. Generate response. Save response. Send response.
                sendToDatabase(message.personEmail.replace('@cisco.com','').replace('@gmail.com',''), message.text)
                # Database definition: Message, From, To.
                response = generateResponse(message.text, message.personEmail)
                #sendToDatabase(response, bot_email, message.personEmail)
                spark.messages.create(toPersonEmail=message.personEmail, text=response)

            else:
                # So not a group message invoking the bot.
                # And not a direct message.
                # So they aren't talking to us. Don't respond.
                return "false"
    return "true"

#TODO: sendToDatabase(), generateResponse().


bot_email = "awstest1@sparkbot.io"
security_email = "spark-cisco-it-admin-bot@cisco.com"
bot_name = "awstest1"
bearer = "MjViMjgwMzQtMGY5MC00MGYwLTk2YmUtNGQwOTc5OTVkODc4ODc3ZDRkY2MtZDA3"
run_itty(server='wsgiref', host='0.0.0.0', port=10010)



def startingInquiries
#Would you like to use a template or start from scratch?


def showTemplates
#Select one of the following templates:

#back

def fromScracth
#How many questions?

#loop for # of questions

def addQuestion
#
