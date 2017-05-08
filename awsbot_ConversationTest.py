from itty import *
import json
from ciscosparkapi import CiscoSparkAPI
import requests
import sys
import os
from generateResponse import generateResponse
from DBconnect import sendToDatabase, pullFromDatabase, createDatabase, deleteDatabase, createTemplate, sendToTemp
import mysql.connector

threadList = []

#object for storing individual conversation threads
class activeThread():
    def __init__(self, roomID, userID, startUpThread, conValue = 0, repeatCounter = 0, reversedCounter = 0, templateName = '', questionList = None, questionCounter = 0, reversedQuestionCounter = 1, tempName = None):
        self.roomID = roomID
        self.userID = userID
        self.conValue = conValue
        self.repeatCounter = repeatCounter
        self.reversedCounter = reversedCounter
        self.templateName = templateName
        self.startUpThread = startUpThread
        self.questionList = questionList
        self.questionCounter = questionCounter
        self.reversedQuestionCounter = reversedQuestionCounter
        self.tempName = tempName
        
    def setConversationValue(self, i):
        self.conValue = i

    def getConversationValue(self):
        return(self.conValue)

    def getRoomID(self):
        return(self.roomID)

    def setRepeatCounter(self, i):
        self.repeatCounter = i
        self.reversedCounter = self.reversedCounter + 1

    def getRepeatCounter(self):
        return(self.repeatCounter)

    def getUserID(self):
        return(self.userID)

    def getReversedCounter(self):
        return(self.reversedCounter)

    def getTemplateName(self):
        return(self.templateName)

    def setTemplateName(self, name):
        self.templateName = name

    def getStartUpThread(self):
        return(self.startUpThread)

    def getQuestionList(self):
        return(self.questionList)

    def setQuestionList(self, i):
        self.questionList = i

    def getQuestionCounter(self):
        return(self.questionCounter)

    def getReversedQuestionCounter(self):
        return(self.reversedQuestionCounter)

    def setQuestionCounter(self, i):
        self.questionCounter = i
        self.reversedQuestionCounter = self.reversedQuestionCounter + 1



#check the index of the active thread in this room:
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

#call after message is "begin" has been reveived to start a new conversation thread
def CreateActiveThread(roomID, userID, messageText, spark):
    i = GetThreadIndex(roomID)
    if i == None:
        #print("no active thread found, created thread for room " + str(roomID))
        threadList.append(activeThread(roomID, userID, True))
        i = GetThreadIndex(roomID)
        NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID, spark)
        #print("created conversation")
    else:
        string1 = str(userID)
        string2 = threadList[i].getUserID()
        if string1 == string2:
            #print("user matches")
            NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID, spark)
        else:
            SendMessage("Someone else already initiated a session in this room, please let them finish the initialization before starting a new one", roomID, spark)

#call after every received message to check if the room is currently involved in a conversation thread
def CheckActiveThread(roomID, userID, messageText, spark):
    i = GetThreadIndex(roomID)
    if i == None:
        print("no active thread found for room " + str(roomID))

    else:
        #check if it's the startup thread
        if(threadList[i].getStartUpThread()):
            string1 = str(userID)
            string2 = threadList[i].getUserID()
            if string1 == string2:
                NextStepInConversation(int(threadList[i].getConversationValue()), i, messageText, roomID, spark)
            else:
                SendMessage("Someone else already initiated a session in this room, please let them finish the initialization before starting a new one", roomID, spark)

        #this means it's a question thread
        else:
            #do stuff in the 1:1 rooms
            NextQuestionInSession(i, messageText, spark, roomID)

#delete conversation thread for roomID with index <index>
def DeleteActiveThread(index, roomID):
    if index == None:
        print("unable to delete active thread for " + str(roomID) + " because no thread exists")
    else:
        del threadList[index]
        print("deleted thread for roomID " + str(roomID))

#Used to determine the flow of conversation during startup process
def NextStepInConversation(conversationState, index, t, roomID, spark):
    #print("next step called")
    messageText = str(t)
    room_name = spark.rooms.get(roomID)

    #start of the chain, response to "begin"
    if(conversationState == 0):
        SendMessage(SetConversationResponseText(0), roomID, spark)
        threadList[index].setConversationValue(1)

    #after receiving answer to "Would you like to start a load a template or start a new template?"
    elif(conversationState == 1):
        if("new template" in messageText):
            SendMessage(SetConversationResponseText(5), roomID, spark)
            threadList[index].setConversationValue(4)

        elif("template" in messageText):
            text = ListTemplates()
            SendMessage(text, roomID, spark) 
            threadList[index].setConversationValue(6) 

        else:
            SendMessage("Sorry I do not recognize that input, please select either blank session or template", roomID, spark)

    #after receiving answer to "How many questions qould you like to include?"
    elif(conversationState == 2):
        text = SetConversationResponseText(2) + str(threadList[index].getReversedCounter()+1)
        SendMessage(text, roomID, spark)
        threadList[index].setRepeatCounter(int(messageText)-1)
        threadList[index].setConversationValue(3)

    #after receiving answer to "please type question #"
    elif(conversationState == 3):
        sendToTemp(threadList[index].getTemplateName(),  messageText)
        if threadList[index].getRepeatCounter() > 0 :
            text = SetConversationResponseText(2) + str(threadList[index].getReversedCounter()+1)
            SendMessage(text, roomID, spark)
            threadList[index].setRepeatCounter(threadList[index].getRepeatCounter()-1)

        else:
            SendMessage(SetConversationResponseText(6), roomID, spark)
            templateList = pullFromDatabase(threadList[index].getTemplateName())
            threadList[index].setQuestionList(templateList)
            StartSession(spark, roomID, room_name, templateList)
            DeleteActiveThread(index, roomID)
        

    #after receiving answer to "Would you like to save this BrainSpark session as a template?"
    elif(conversationState == 4):
        if(MatchTemplate):
            threadList[index].setTemplateName(messageText)
            createTemplate(messageText)
            SendMessage(SetConversationResponseText(1), roomID, spark)
            threadList[index].setConversationValue(2)

        else:
            SendMessage("Sorry, this template name is already in use, please provide a different name", roomID, spark)

    #after receiving answer to "What name would you like to use for this template?"
    elif(conversationState == 5):
        if(MatchTemplate(messageText)):
            StoreTemplate(messageText)
            SendMessage(SetConversationResponseText(6), roomID, spark)
            StartSession(spark, roomID, room_name, threadList[index].getQuestionList())
            DeleteActiveThread(index, roomID)
        
        else:
            SendMessage(SetConversationResponseText(10), roomID, spark)

    #after receiving answer to "Which template would you like to use?"
    elif(conversationState == 6):
        if("new template" in messageText):
            SendMessage(SetConversationResponseText(5), roomID, spark)
            threadList[index].setConversationValue(4)

        else:
            if(MatchTemplate(messageText)):
                text = ListQuestions(messageText, index)
                SendMessage(text, roomID, spark)
                threadList[index].setConversationValue(7)
            else:
                SendMessage(SetConversationResponseText(10), roomID, spark)

   #after receiving answer to "Would you like to start a session with this template?"
    elif(conversationState == 7):
        if("no" in messageText):
            SendMessage(SetConversationResponseText(9), roomID, spark)
            DeleteActiveThread(index, roomID)

        elif("yes" in messageText):
            SendMessage(SetConversationResponseText(4), roomID, spark)
            StartSession(spark, roomID, room_name, threadList[index].getQuestionList())
            DeleteActiveThread(index, roomID)
            

#Used to determine the correct question
def NextQuestionInSession(index, messageText, spark, roomID):
    i = threadList[index].getQuestionCounter

    if threadList[index].getQuestionCounter() > 0 :
        text = threadList[index].getQuestionList()[threadList[index].getReversedQuestionCounter()]
        SendPersonalMessage(text, roomID, spark)
        threadList[index].setQuestionCounter(threadList[index].getQuestionCounter()-1)

    else:
        SendPersonalMessage("That's all questions, time to start feedback", roomID, spark)

#used to set the basic text for the next response
def SetConversationResponseText(conversationValue):
    if(conversationValue == 0):
        return("Would you like to start a load a template or start a new template?")

    elif(conversationValue == 1):
        return("How many questions would you like to include?")

    elif(conversationValue == 2):
        return("Please type question ")

    elif(conversationValue == 3):
        return("Would you like to save this BrainSpark session as a template?")

    elif(conversationValue == 4):
        return("OK! Let's start!")

    elif(conversationValue == 5):
        return("What name would you like to use for the template? (due to a bug, please make sure the name doesn't include 'end', even in a word like 'agenda'. This will be fixed asap)")

    elif(conversationValue == 6):
        return("Thanks for the input! The template has been saved. Let's start!")

    elif(conversationValue == 7):
        return("Which template would you like to use? Pick from the following:")

    elif(conversationValue == 8):
        return("Would you like to start a session with this template? It contains the following questions: ")

    elif(conversationValue == 9):
        return("No problem! Let me know when you want to start a new session.")

    elif(conversationValue == 10):
        return("I'm sorry, there is no template with that name, please try again")

#Send a message using <text> as the content
def SendMessage(text, room_id, spark):
    spark.messages.create(roomId=room_id, text=text)

def SendPersonalMessage(text, personalEmail, spark):
    spark.messages.create(toPersonEmail=personalEmail, text=text)

#Starts the BrainSpark session
def StartSession(spark, room_id, room_name, qList):
    memberList = spark.memberships.list(roomId=room_id)
    GROUP_MESSAGE = "Brainstorming session for '%s' is starting." % (room_name.title)
    spark.messages.create(roomId=room_id, text=GROUP_MESSAGE) # Message the room.
    for Membership in memberList: # Message each member in the room individually.
        if Membership.personEmail != bot_email and Membership.personEmail != security_email: # filter out the bot and cisco security bot, we dont want to send them a message!
            INTRO_MESSAGE = "You have been invited to brainstorming session '%s'. Type 'help' for a brief introduction on how I work!" % (room_name.title)
            spark.messages.create(toPersonEmail=Membership.personEmail, text=INTRO_MESSAGE)            
            spark.messages.create(toPersonEmail=Membership.personEmail, text=qList[0])
            threadList.append(activeThread(Membership.personEmail, Membership.personEmail, False, questionList=qList, questionCounter = len(qList)-1))
            print("dit gaat goed")
            createDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
            print("als alles goed is zou er nu een db gemaakt moeten zijn")
    
#placeholder for storing the template <NO LONGER NEEDED?>
def StoreTemplate(name):
    print("stored template with name " + name)

#returns a string with a list of all the templates
def ListTemplates():
    templateList = pullFromDatabase("Templates")
    text = SetConversationResponseText(7)
            
        #list the templates and add them as new lines to the text string
    for i, s in enumerate(templateList):
        text += ("\n" + s)

    return text

#returns a string with a list of all the questions in template <dbName>
def ListQuestions(dbName, i):
    templateList = pullFromDatabase(dbName)
    threadList[i].setQuestionList(templateList)
    text = SetConversationResponseText(8)
            
        #list the templates and add them as new lines to the text string
    for i, s in enumerate(templateList):
        text += ("\n" + s)

    return text


#Makes sure that template <name> exists in the database
def MatchTemplate(name):
    templateList = pullFromDatabase("Templates")
    if any(name in s for s in templateList):
        print("template found")
        return True

    else:
        print("no match")
        return False

#used to end the session
def EndSession():
    print("ending session")

#Used for processing the webhooks
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
            CreateActiveThread(room_id, message.personEmail, in_message, spark) 

        elif message.roomType == "group":
            CheckActiveThread(room_id, message.personEmail, in_message, spark)

        # looks for personal messages in 1:1 conversations. These messages need to be saved to our database
        else:

            if message.roomType == "direct":
                if in_message == "help":
                    spark.messages.create(toPersonEmail=message.personEmail, text="explanation of how this works, what is your idea")
                    return "true"
                #Temp making sure it tries to do this:
                
                

                # TODO: Save message. Generate response. Save response. Send response.
                sendToDatabase(message.personEmail.replace('@cisco.com','').replace('@gmail.com',''), message.text)
                CheckActiveThread(message.personEmail, message.personEmail, in_message, spark)
                # Database definition: Message, From, To.
                #response = generateResponse(message.text, message.personEmail)
                #sendToDatabase(response, bot_email, message.personEmail)
                #spark.messages.create(toPersonEmail=message.personEmail, text=response)

            else:
                # So not a group message invoking the bot.
                # And not a direct message.
                # So they aren't talking to us. Don't respond.
                return "false"
    return "true"


#Basic variables
bot_email = "awstest1@sparkbot.io"
security_email = "spark-cisco-it-admin-bot@cisco.com"
bot_name = "awstest1 "
bearer = "MjViMjgwMzQtMGY5MC00MGYwLTk2YmUtNGQwOTc5OTVkODc4ODc3ZDRkY2MtZDA3"
run_itty(server='wsgiref', host='0.0.0.0', port=10010)