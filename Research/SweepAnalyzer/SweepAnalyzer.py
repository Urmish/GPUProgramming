#!/usr/bin/python
import sys
import re
import argparse
import os
import itertools
from subprocess import call

totalTests = dict([('Test12.txt',1),
		   ('Test13.txt',1),
		   ('Test14.txt',1),
		   ('Test15.txt',3),
		   ('Test16.txt',3),
		   ('Test18.txt',4),
		   ('Test20.txt',2),
		   ('Test2.txt' ,1),
		   ('Test3.txt' ,3),
		   ('Test4.txt' ,6)])


for key in totalTests:
  try:
    fileHandler = open("TestCases/"+key, "r")
  except IOError:
    print "Cannot Open File "+"TestCases/"+key
    sys.exit()
  
  fileArray = []
  bratioArrayIndex = dict()
  lineNum=0
  for line in fileHandler:
    fileArray.append(line)
    match = re.finditer("(BRATIO[ABD]\d)",line)
    for a in match:
      if(a.group(0) in bratioArrayIndex):
	bratioArrayIndex[a.group(0)].append(lineNum)
      else:
	bratioArrayIndex[a.group(0)] = [lineNum]
    lineNum=lineNum+1

  print bratioArrayIndex
  print "********************"
  fileHandler.close()
