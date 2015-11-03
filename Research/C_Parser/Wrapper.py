#!/usr/bin/python
import sys
import re
import argparse
import os
import itertools
from subprocess import call

try:
  parser = argparse.ArgumentParser(description='Reads inputs to Static Serial Code Analyzer')
  parser.add_argument('-file',required=True, dest='file_name',help='file that you want analyzed')
  args = parser.parse_args()
  fileListHandler = open(args.file_name, "r")
except IOError:
  print "There was an error reading ", args.file_name
  sys.exit()

for currentLine in fileListHandler:
  print currentLine
  command = "python "+os.getcwd()+"/Parser.py -file "+os.getcwd()+"/"+currentLine.rstrip()
  print command.split(" ")
  call(command.split(" "))


try:
  fileOutputHandler = open("Output.txt", "r")
except IOError:
  print "There was an error reading Output.txt"
  sys.exit()

try:
  fileKeyHandler = open("../key", "r")
except IOError:
  print "There was an error reading ", args.file_name
  sys.exit()

listErrors = ['Name','Transcedentals','CompInt','Coallesced','Lbdiv32','Lbdiv1024','fmuldiv','ilp16384','numThreads','criticalPath']
listErrorValues = [0,0,0,0,0,0,0,0,0,0]
listErrorsTest = ['','','','','','','','','','']
for lineOutput, lineKey in zip(fileOutputHandler, fileKeyHandler):
  lineOutput = lineOutput.rstrip()
  lineKey = lineKey.rstrip()
  lineOutputList = lineOutput.split(',')
  lineKeyList = lineKey.split(',')
  testName = ""
  #print lineOutputList
  #print lineKeyList
  #print len(lineOutputList)
  #print range(len(lineOutputList))
  for i in range(len(lineOutputList)): 
    if i==0:
      if(lineOutputList[i] != lineKeyList[i]):
        print "ERROR! Test name should be same"
        sys.exit()
    else:
      if(lineOutputList[i] != lineKeyList[i]):
        listErrorValues[i] = listErrorValues[i]+1
	listErrorsTest[i] = listErrorsTest[i] + " " + lineKeyList[0]

for i in range(len(listErrorValues)):
  if i>0:
    print listErrors[i]," - ",listErrorValues[i],"/23 Failing Tests - ",listErrorsTest[i]
