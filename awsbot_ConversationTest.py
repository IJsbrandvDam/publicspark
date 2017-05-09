from itty import *
import json
from ciscosparkapi import CiscoSparkAPI
import requests
import sys
import os
from generateResponse import generateResponse
from DBconnect import sendToDatabase, pullFromDatabase, createDatabase, deleteDatabase, createTemplate, sendToTemp, pullAnswersFromDatabase
import mysql.connector
import copy

threadList = []

#object for storing individual conversation threads
class activeThread():
    def __init__(self, roomID, userID, startUpThread, conValue = 0, repeatCounter = 0, reversedCounter = 0, templateName = '', questionList = None, questionCounter = 0, reversedQuestionCounter = 1, tempName = None, groupMembers = None, parentIndex = None, feedbackCounter = 0, finishedCounter = 0, finished = False):
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
        self.groupMembers = groupMembers
        self.parentIndex = parentIndex
        self.feedbackCounter = feedbackCounter
        self.score = []
        self.finishedCounter = finishedCounter
        self.finished = finished
        self.averageScore = 0
        self.winningDB = ""

        
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

    def getGroupMembers(self):
        return(self.groupMembers)

    def setGroupMembers(self,members):
        self.groupMembers=members

    def getParentIndex(self):
        return(self.parentIndex)

    def KillChildren(self, spark):
        if self.groupMembers != None:
            for i, s in enumerate(self.groupMembers):
                q = GetThreadIndex(s)
                r = threadList[q].getRoomID()

                AverageScoreUser(r)
                
                DeleteActiveThread(q, s, spark)

        else:
            print("no children found")

    def getFeedbackCounter(self):
        return(self.feedbackCounter)

    def setFeedbackCounter(self, i):
        self.feedbackCounter = i

    def getScore(self):
        return(self.score)

    def setScore(self,i):
        self.score.append(int(i))

    def setFinishedCounter(self,i):
        self.finishedCounter = i

    def getFinishedCounter(self):
        return(self.finishedCounter)

    def setFinished(self, i):
        self.finished = i

    def getFinished(self):
        return(self.finished)

    def setAverageScore(self, i):
        self.averageScore = i

    def getAverageScore(self):
        return(self.averageScore)

    def getWinningDB(self):
        return(self.winningDB)

    def setWinningDB(self, i):
        self.winningDB = i


def AverageScoreUser(roomID):
    i = GetThreadIndex(roomID)
    score = threadList[i].getScore()

    for l, s in enumerate(score):
        print("score = " + str(s))
        try:
            s = int(s)
        except:
            s = 0
        s = int(s)
        print("score als int is " + str(s))
        score[l] = s

    a = sum(score)/len(score)

    if threadList[threadList[index].getParentIndex()].getAverageScore() < a:      
        db = copy.copy(roomID)
        db.replace("@cisco.com", "")
        db.replace("@gmail.com", "")
        threadList[threadList[index].getParentIndex()].setAverageScore(a)
        threadList[threadList[index].getParentIndex()].setWinningDB(db)



#check the index of the active thread in this room:
def GetThreadIndex(messageRoom):
    hasActive = False
    index = -1
    activeIndex = None

    for objects in threadList:
        index = index + 1
        if messageRoom in objects.getRoomID():
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

def CleanFeedback(feedbackList, amount):
    text = "Please provide feedback to the following answers:"
    for i, s in enumerate(feedbackList):
        if i < amount:
            text += ("\n \n" + s)

    return(text)            
            
#delete conversation thread for roomID with index <index>
def DeleteActiveThread(index, roomID, spark):
    if index == None:
        print("unable to delete active thread for " + str(roomID) + " because no thread exists")
    else:
        threadList[index].KillChildren(spark)
        SendMessage(str(threadList[index].getWinningDB), roomID, spark)
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
            StartSession(spark, roomID, room_name, templateList, index)

        

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
            StartSession(spark, roomID, room_name, threadList[index].getQuestionList(), index)
        
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

        elif("yes" in messageText):
            SendMessage(SetConversationResponseText(4), roomID, spark)
            StartSession(spark, roomID, room_name, threadList[index].getQuestionList(),index)
            

#Used to determine the correct question
def NextQuestionInSession(index, messageText, spark, roomID):
    i = threadList[index].getQuestionCounter

    if threadList[index].getQuestionCounter() > 99:
        if threadList[index].getFinished() == False:
            feedbackSession(index, messageText, spark, roomID)


    elif threadList[index].getQuestionCounter() > 0 :
        text = threadList[index].getQuestionList()[threadList[index].getReversedQuestionCounter()]
        SendPersonalMessage(text, roomID, spark)
        threadList[index].setQuestionCounter(threadList[index].getQuestionCounter()-1)

    else:
        SendPersonalMessage("That's all questions, please wait until everyone finished!", roomID, spark)
        threadList[index].setQuestionCounter(100)
        feedbackCounter = threadList[threadList[index].getParentIndex()].getFeedbackCounter()
        threadList[threadList[index].getParentIndex()].setFeedbackCounter(feedbackCounter+1)
        print(str(threadList[index].getFinished()))
        if threadList[index].getFinished() == False:
            print("passed line 315")
            feedbackSession(index, messageText, spark, roomID)


def feedbackSession(index, messageText, spark, roomID):
    i = None
    q = None
    w = None
    cleanGroupEmails = None
    cleanGroupUsers = None

    l = len(threadList[threadList[index].getParentIndex()].getQuestionList())
    i = copy.copy(threadList[threadList[index].getParentIndex()].getGroupMembers())
    print(i)

    q = copy.copy(i)
    w = copy.copy(i)

    for a, s in enumerate(q):
        s = str(s)
        s = s.replace("(u'", "")
        s = s.replace("',)", "")
        q[a] = s

    cleanGroupEmails = q

    print(cleanGroupEmails)

    for a, s in enumerate(w):
        s = str(s)
        s = s.replace("(u'", "")
        s = s.replace("',)", "")
        s = s.replace("@cisco.com", "")
        s = s.replace("@gmail.com", "")
        w[a] = s
    
    cleanGroupUsers = w
    print(cleanGroupUsers)

    print(threadList[index].getQuestionCounter())

    if threadList[index].getQuestionCounter() - 100 < len(cleanGroupUsers):
        dbName = cleanGroupUsers[threadList[index].getQuestionCounter() - 100]
        print("passed line 357")
        feedbackCounter = threadList[threadList[index].getParentIndex()].getFeedbackCounter()

        if feedbackCounter == len(i):
            print("passed line 361")
            for a, s in enumerate(cleanGroupEmails):
                print(str(s))
                SendPersonalMessage("All answers are in, ready to start with feedback?", str(s), spark)
            threadList[threadList[index].getParentIndex()].setFeedbackCounter(feedbackCounter+1)
        elif feedbackCounter > len(i):
            try:
                threadList[GetThreadIndex(cleanGroupUsers[threadList[index].getQuestionCounter() - 101])].setScore(messageText)
            except ValueError:
                pass
            print(str(threadList[GetThreadIndex(cleanGroupUsers[threadList[index].getQuestionCounter() - 101])].getScore()))
            # if threadList[threadList[index].getQuestionCounter() - 101] >= 0:
            #     threadList[threadList[index].getQuestionCounter() - 101].setScore(messageText)
            # print(threadList[threadList[index].getQuestionCounter() - 101].getScore())
            if dbName in roomID:
                threadList[index].setQuestionCounter(threadList[index].getQuestionCounter() + 1)
                if threadList[index].getQuestionCounter() - 100 < len(cleanGroupUsers):
                    dbName = cleanGroupUsers[threadList[index].getQuestionCounter() - 100]
                    text = pullAnswersFromDatabase(dbName)
                    SendPersonalMessage(CleanFeedback(text, l), roomID, spark)
                    threadList[index].setQuestionCounter(threadList[index].getQuestionCounter() + 1)
                else:
                    finishedCounter = threadList[threadList[index].getParentIndex()].getFinishedCounter()
                    threadList[threadList[index].getParentIndex()].setFinishedCounter(finishedCounter+1)
                    threadList[index].setFinished(True)
                    EndSession()
            else:   
                text = pullAnswersFromDatabase(dbName)
                SendPersonalMessage(CleanFeedback(text, l), roomID, spark)
                threadList[index].setQuestionCounter(threadList[index].getQuestionCounter() + 1)
        else:
            print("passed line 392")
            return
    
    else:
        try:
            threadList[GetThreadIndex(cleanGroupUsers[threadList[index].getQuestionCounter() - 101])].setScore(messageText)
        except ValueError:
            pass
        finishedCounter = threadList[threadList[index].getParentIndex()].getFinishedCounter()
        threadList[threadList[index].getParentIndex()].setFinishedCounter(finishedCounter+1)
        threadList[index].setFinished(True)
        EndSession()

    finishedCounter = threadList[threadList[index].getParentIndex()].getFinishedCounter()
    if finishedCounter == len(i):
        QuitSession(spark, threadList[threadList[index].getParentIndex()].getRoomID())
            


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
        return("What name would you like to use for the template?")

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
def StartSession(spark, room_id, room_name, qList, index):
    memberList = spark.memberships.list(roomId=room_id)
    GROUP_MESSAGE = "Brainstorming session for '%s' is starting." % (room_name.title)
    spark.messages.create(roomId=room_id, text=GROUP_MESSAGE) # Message the room.
    groupMembers = []
    for Membership in memberList: # Message each member in the room individually.
        if Membership.personEmail != bot_email and Membership.personEmail != security_email: # filter out the bot and cisco security bot, we dont want to send them a message!
            INTRO_MESSAGE = "You have been invited to brainstorming session '%s'. Type 'help' for a brief introduction on how I work!" % (room_name.title)
            createDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
            groupMembers.append(Membership.personEmail)
            spark.messages.create(toPersonEmail=Membership.personEmail, text=INTRO_MESSAGE)            
            spark.messages.create(toPersonEmail=Membership.personEmail, text=qList[0])
            threadList.append(activeThread(Membership.personEmail, Membership.personEmail, False, questionList=qList, questionCounter = len(qList)-1, parentIndex = index))
            #print("dit gaat goed")
            #createDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
            #print("als alles goed is zou er nu een db gemaakt moeten zijn")
    threadList[index].setGroupMembers(groupMembers)
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

def QuitSession(spark, roomID):
    room_name = spark.rooms.get(roomID) # retrieve room information to get the room name
    personName = spark.people.list()


    memberList = spark.memberships.list(roomId=roomID)
    GROUP_MESSAGE = "Brainstorming session for '%s' is ending." % (room_name.title)
    index = GetThreadIndex(roomID)
    DeleteActiveThread(index, roomID, spark)
    spark.messages.create(roomId=roomID, text=GROUP_MESSAGE) # Message the room.
    for Membership in memberList: # Message each member in the room individually.
        if Membership.personEmail != bot_email and Membership.personEmail != security_email:
            END_MESSAGE = "Brainstorming session '%s' is ending." % (room_name.title)
            spark.messages.create(toPersonEmail=Membership.personEmail, text=END_MESSAGE)
            deleteDatabase(Membership.personEmail.replace('@cisco.com', '').replace('@gmail.com',''))
    #TODO: Send the best idea to the group chat.
    BEST_IDEA = "The best idea." #getBestIdea(room_id)
    spark.messages.create(roomId=roomID, text=BEST_IDEA)

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
        elif message.roomType == "group" and "end session" in in_message:
            memberList = spark.memberships.list(roomId=room_id)
            GROUP_MESSAGE = "Brainstorming session for '%s' is ending." % (room_name.title)
            index = GetThreadIndex(room_id)
            DeleteActiveThread(index, room_id, spark)
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
bot_email = "brainspark@sparkbot.io"
security_email = "spark-cisco-it-admin-bot@cisco.com"
bot_name = "BrainSpark"
bearer = "MGI0MWMyMDktMGIyZC00MzAxLWEyYzAtN2U2ZTA5YjQ5N2RkZTE0NjZkODgtMTJh"
run_itty(server='wsgiref', host='0.0.0.0', port=10010)
