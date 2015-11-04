#!/usr/bin/python
import sys
import re
import argparse
import os
import itertools
import collections
from subprocess import call
import itertools

def drange(start, stop, step):
    while start <= stop:
            yield start
            start += step

totalTests = dict([('Test12.txt',1),
		   ('Test13.txt',1),
		   ('Test14.txt',1),
		   ('Test15.txt',3),
		   ('Test16.txt',3),
		   ('Test18.txt',4),
		   ('Test20.txt',2),
		   ('Test2.txt' ,1),
		   ('Test3.txt' ,3),])
		   #('Test4.txt' ,6)])


for key in totalTests:
  listOfValues = []
  try:
    fileHandler = open("TestCases/"+key, "r")
  except IOError:
    print "Cannot Open File "+"TestCases/"+key
    sys.exit()
  
  fileArray = []
  bratioSet = []
  bratioPerLine = dict()
  lineNum=0
  for line in fileHandler:
    fileArray.append(line)
    match = re.finditer("(BRATIO\d[AB])",line)
    for a in match:
      if(lineNum in bratioPerLine):
	if ((a.group(0) in bratioSet) == False) :
	  bratioSet.append(a.group(0))
	bratioPerLine[lineNum].append(a.group(0))
      else:
	if ((a.group(0) in bratioSet) == False) :
	  bratioSet.append(a.group(0))
	bratioPerLine[lineNum] = [a.group(0)]
    match = re.finditer("(BRATIO\dD)",line)
    for a in match:
      if(lineNum in bratioPerLine):
	bratioPerLine[lineNum].append(a.group(0))
      else:
	bratioPerLine[lineNum] = [a.group(0)]

    lineNum=lineNum+1

  bratioSort = sorted(bratioSet)
  print key
  print "----"
  print bratioSort
  print bratioPerLine
  
  for ratios in bratioSort:
    l = []
    for i in drange(0.0,1.0,0.25):
      l.append(ratios+str(i))
    listOfValues.append(l)
  crossProduct = listOfValues[0]
  if len(listOfValues) > 1:
    crossProduct = list(itertools.product(*listOfValues))
  print (crossProduct)
  print "********************"
  for eachP in crossProduct:
    testName = re.sub("\.txt","",key)
    suffix = ""
    if (isinstance(eachP,str)):
      eachP = [eachP]
    for eachi in eachP:
      eachisuffix = re.sub("\.","",eachi)
      suffix=suffix+"_"+eachisuffix
    fileWrite = open("temp/"+testName+suffix+".txt","w")
    for ln in range(0,lineNum):
      if ln in bratioPerLine:
	modifiedLine = fileArray[ln]
	for eachi in eachP:
	  branchId = re.search("(BRATIO\d[AB])",eachi)
	  subi = re.sub(r'(\d)[AB]','\1',eachi)
	  modifiedLine = re.sub(branchId.group(0),subi,modifiedLine)
	  if ((bool(re.search("BRATIO\dB",eachi)) == True) and (bool(re.search("BRATIO\dD",modifiedLine)))):
	    branchId = re.search("(BRATIO)\dB(\d+\.\d+)",eachi)
	    val = 1 - float(branchId.group(1))
	    subValue = branchId.group(0)+"D"+str(val)
	    modifiedLine = re.sub(branchId.group(0)+"D",subValue,modifiedLine)
	fileWrite.write(modifiedLine)
      else:
	fileWrite.write(fileArray[ln])
    fileWrite.close()
  fileHandler.close()
