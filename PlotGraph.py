import pandas as pd
import matplotlib.pyplot as plt
import sys

#take input from terminal, simply change the sys.argv for whatever input from the message
finInput = sys.argv[1]
susInput = sys.argv[2]

#read & prepare the csv file
df = pd.read_csv('UseFromModel.csv')
df.head()

#convert text input to the correct values in the table
def ConvertValues(s):
	if(s == "5%"):
		return 1
	elif(s == "10%"):
		return 2
	elif(s == "20%"):
		return 3
	elif(s == "30%"):
		return 4
	elif(s == "40%"):
		return 5
	elif(s == "50%"):
		return 6
	elif(s == "60%"):
		return 7
	elif(s == "70%"):
		return 8
	elif(s == "80%"):
		return 9
	elif(s == "90%"):
		return 10
	elif(s == "100%"):
		return 11
	elif(s == "110%"):
		return 12
	elif(s == "120%"):
		return 13
	elif(s == "130%"):
		return 14
	elif(s == "140%"):
		return 15
	elif(s == "150%"):
		return 16		

#apply conversion and calculate which line to use
def CalculateGraphValue():
	financialMod = ConvertValues(finInput)
	sustainableMod = ConvertValues(susInput)

	i=df[str((16*(sustainableMod-1))+financialMod)]
	return i

#plot, format and save the histogram
def PlotGraph(i):
	plt.hist(i,histtype='bar',orientation='vertical')
	plt.title('Routine use from model')
	plt.ylabel('count')
	plt.xlabel('use')
	plt.savefig('histogram.png')

#execution
x = CalculateGraphValue()
PlotGraph(x)
