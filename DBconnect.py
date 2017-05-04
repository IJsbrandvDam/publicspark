import mysql.connector
import string

def createDatabase(personName):
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("CREATE TABLE %s (Question INT PRIMARY KEY AUTO_INCREMENT, Answer TEXT)" % (personName))
	conn.commit()
	return "true"


def deleteDatabase(personName):
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("DROP TABLE IF EXISTS %s" % (personName))
	conn.commit()
	return "true"


def sendToDatabase(personName,answer):
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("INSERT INTO %s (Answer) VALUES ('%s')" % (personName,answer))
	conn.commit()
	return "true"
# print(mycursor.fetchall())

def pullFromDatabase():
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	results = None
	sql = "SELECT Question FROM Templates"
	try:
		mycursor.execute(sql)
		results = mycursor.fetchall()
		#print (results)
	except:
		print "Nothing found"
	conn.commit()

	for i, s in enumerate(results):
		s = str(s)
		s = s.replace("(u'", "")
		s = s.replace("',)", "")
		results[i] = s
		

	return results


# def createTemplateDB(tempName):
# 	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
#                               host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
#                               database='brainspark')
# 	mycursor=conn.cursor()
# 	mycursor.execute("CREATE TABLE Templates (Question INT PRIMARY KEY AUTO_INCREMENT, Name TEXT)")
# 	conn.commit()
# 	return "true"



def createTemplate(tempName):
	s = stripWhiteSpace(tempName)
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("CREATE TABLE '%s' (Question INT PRIMARY KEY AUTO_INCREMENT, Answer TEXT)" % (s))
	mycursor.execute("INSERT INTO Templates (Question) VALUES ('%s')" % (tempName))
	conn.commit()
	return "true"

def sendToTemp(tempName,question):
	s = stripWhiteSpace(tempName)
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("INSERT INTO %s (Answer) VALUES ('%s')" % (s,question))
	conn.commit()
	return "true"

def stripWhiteSpace(stringText):
	print("begonnen met strippen van: " + stringText)
	s = stringText
	whitespace = " "
	for whitespace in string.s:
		s.replace(" ", "")

	print("klaar, eindresultaat is: " + s)
	return s








# createDatabase("chris")
#deleteDatabase("ctsioura")
# sendToDatabase("chris","bla bla bla")
x = pullFromDatabase()

print(pullFromDatabase())
print(x[0])
print(x[1])
