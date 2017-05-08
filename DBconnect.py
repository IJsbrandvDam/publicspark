import mysql.connector

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

def pullFromDatabase(dbName):
	s = stripWhiteSpace(dbName)
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	results = None
	sql = "SELECT Question FROM %s" % (s)
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

#Create new template in the database
def createTemplate(tempName):
	s = stripWhiteSpace(tempName)
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	print("created tempalte with name: " + s)
	mycursor.execute("CREATE TABLE %s (nummer INT PRIMARY KEY AUTO_INCREMENT, Question TEXT)" % (s))
	mycursor.execute("INSERT INTO Templates (Question) VALUES ('%s')" % (tempName))
	conn.commit()
	return "true"

#Store questions in the template database
def sendToTemp(tempName,question):
	s = stripWhiteSpace(tempName)
	conn = mysql.connector.connect(user='brainspark', password='C!sco123',
                              host='brainspark.cptvcix7ijfy.us-west-2.rds.amazonaws.com',
                              database='brainspark')
	mycursor=conn.cursor()
	mycursor.execute("INSERT INTO %s (Question) VALUES ('%s')" % (s,question))
	conn.commit()
	return "true"

#remove the spaces from the template name
def stripWhiteSpace(stringText):
	s = stringText.replace(" ", "")
	return s
