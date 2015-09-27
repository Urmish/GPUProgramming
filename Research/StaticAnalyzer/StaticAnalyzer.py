#!/usr/bin/python
import sys
import re

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
  return

print "Hi, This is a Static Code Analyzer. Please Use Python 2.7 or later version"
try:
  # open file stream
  file_name = "/afs/cs.wisc.edu/u/u/t/uthakker/Documents/StaticAnalyzerInput/Input1.txt"
  fileHandler = open(file_name, "r")
except IOError:
  print "There was an error reading ", file_name
  sys.exit()

for currentLine in fileHandler:
  printFileLine(currentLine)
  if isStartOfAnnotation(currentLine) :
    print "Start Analyzing"
  
  if isEndOfAnnotation(currentLine) :
    print "End Analyzing" 
    break
