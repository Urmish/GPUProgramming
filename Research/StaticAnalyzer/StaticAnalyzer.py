#!/usr/bin/python
import sys
import re
import argparse

###################################Function and Class Definition Starts Here################################################################
class Stack():
  def __init__(self):
    self.items = []
    
  def isEmpty(self):
    return self.items == []
    
  def push(self, item):
    return self.items.append(item)
  
  def pop(self):
    return self.items.pop()
  
  def getElements(self):
    return self.items

  def front(self):
    Obj = self.pop()
    self.push(Obj)
    return Obj

scope = Stack()
scope.push('Global')

def isStartOfAnnotation(currentLine):
  "This function checks for start of an annotated code"
  matchObj = re.search('Annotation Begin',currentLine, re.I)
  if matchObj:
    print "Annotation Begin Found"
    return True
  else:
    return False
 
def isEndOfAnnotation(currentLine):
  "This function checks for end of an annotated code"
  matchObj = re.search('Annotation End',currentLine, re.I)
  if matchObj:
    print "Annotation End Found"
    return True
  else:
    return False

def printFileLine(currentLine):
  "This function simply prints the current line of the function"
  print currentLine
  return

def getVariables(currentLine):
  "This function looks for variable declaration and tries to understand their type"
  matchObjInt = re.search('int ',currentLine, re.I)
  matchObjFloat = re.search('float ',currentLine, re.I)
  matchObjDouble = re.search('double ',currentLine, re.I)
  if matchObjInt:
    print "Found an Int Variable"
  if matchObjFloat:
    print "Found a Float Variable"
  if matchObjDouble:
    print "Found a Double Variable"
  return
###################################Function and Class Definition Ends Here################################################################

print "**************************************************************************"
print "****			Static Code Analyzer			      ****"
print "**************************************************************************"
print "****		   Please Use Python 2.7 or later		      ****"
print "**************************************************************************"
try:
  # open file stream
  parser = argparse.ArgumentParser(description='Reads inputs to Static Serial Code Analyzer')
  parser.add_argument('-file',required=True, dest='file_name',help='file that you want analyzed')
  args = parser.parse_args()
  #file_name = "/afs/cs.wisc.edu/u/u/t/uthakker/Documents/StaticAnalyzerInput/Input1.txt"
  fileHandler = open(args.file_name, "r")
except IOError:
  print "There was an error reading ", args.file_name
  sys.exit()

for currentLine in fileHandler:
  printFileLine(currentLine)
  getVariables(currentLine)
  if isStartOfAnnotation(currentLine) :
    print "Start Analyzing"
  
  if isEndOfAnnotation(currentLine) :
    print "End Analyzing" 
    break
