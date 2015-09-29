#!/usr/bin/python
import sys
import re
import argparse

variables = dict()
TotalTranscendentals = 0
TotalArithmeticInstructions = 0
StartAnalyzing = False
previousLine = ""
NumLoadOperations = 0
NumStoreOperations = 0
NumOffsetAccesses = 0
NumIndirectAccesses = 0 #A[B[i]]
###################################Function and Class Definition Starts Here################################################################
class VariableState():
  def __init__(self,name,scope,varType,size,value):
    self.name = name
    self.scope = scope
    self.varType = varType #0 - Int, 1 - Float, 2 - Double
    self.size = size
    self.value = value
    return None
  
  def printValues(self):
    print "The values of this entry are"
    print "Name -     ",self.name
    print "Scope -    ",self.scope
    print "varType -  ",self.varType
    print "size -     ",self.size
    print "value-     ",self.value
    return None

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

scope = Stack() #Accessed to understand the scope of a variable
scope.push('Global')

def printVariables():
    print "**********"
    for key in variables:
      variables[key].printValues()
      print "**********"
    return True

def pushVariables(name,
		  varType,
		  size,
		  value):
  #name - Name of the variable, varType - int/float/double, size - scalar has size 1, array has size > 1, value - for a scalar, value if assigned, else None
  #varType 0 - Int, 1 - Float, 2 - Double
  "This function pushes the variables and its associated properties to dictionary variables"
  variables[name] = VariableState(name,scope.front(),varType,size,value)
  return True

def isStartOfAnnotation(currentLine):
  "This function checks for start of an annotated code"
  matchObj = re.search('Annotation Begin',currentLine, re.I)
  if matchObj:
    print "Annotation Begin Found"
    global StartAnalyzing
    StartAnalyzing = True
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
    #print "Found an Int Variable"
    matchObjIntArray       = re.search('int (\w+)\[(\d+)\]',currentLine, re.I)
    matchObjIntScalar      = re.search('int (\w+)',currentLine, re.I)
    matchObjIntScalarValue = re.search('=\D*(\d+)',currentLine, re.I)
    intName = ""
    intVarType = 0
    intSize = 0
    intValue = None
    if matchObjIntArray:
      #print "Its an array with Name - ",matchObjIntArray.group(1)," and Size - ",matchObjIntArray.group(2)
      intName = matchObjIntArray.group(1)
      intSize = matchObjIntArray.group(2)
    elif matchObjIntScalar:
      #print "Its a Scalar with Name ",matchObjIntScalar.group(1)
      intName = matchObjIntScalar.group(1)
      intSize = 1
    if matchObjIntScalarValue:
      #print "And Value ",matchObjIntScalarValue.group(1)
      intValue = matchObjIntScalarValue.group(1)
    pushVariables(intName,
                  intVarType,
                  intSize,
                  intValue)
  if matchObjFloat:
    #print "Found a Float Variable" 
    matchObjFloatArray       = re.search('float (\w+)\[(\d+)\]',currentLine, re.I)
    matchObjFloatScalar      = re.search('float (\w+)',currentLine, re.I)
    matchObjFloatScalarValue = re.search('=\D*(\d+)',currentLine, re.I)
    floatName = ""
    floatVarType = 0
    floatSize = 0
    floatValue = None
    if matchObjFloatArray:
      #print "Its an array with Name - ",matchObjFloatArray.group(1)," and Size - ",matchObjFloatArray.group(2)
      floatName = matchObjFloatArray.group(1)
      floatSize = matchObjFloatArray.group(2)
    elif matchObjFloatScalar:
      #print "Its a Scalar with Name ",matchObjFloatScalar.group(1)
      floatName = matchObjFloatScalar.group(1)
      floatSize = 1
    if matchObjFloatScalarValue:
      #print "And Value ",matchObjFloatScalarValue.group(1)
      floatValue = matchObjFloatScalarValue.group(1)
    pushVariables(floatName,
                  floatVarType,
                  floatSize,
                  floatValue)
 
  if matchObjDouble:
    #print "Found a Double Variable"
    matchObjDoubleArray       = re.search('double (\w+)\[(\d+)\]',currentLine, re.I)
    matchObjDoubleScalar      = re.search('double (\w+)',currentLine, re.I)
    matchObjDoubleScalarValue = re.search('=\D*(\d+)',currentLine, re.I)
    doubleName = ""
    doubleVarType = 0
    doubleSize = 0
    doubleValue = None
    if matchObjDoubleArray:
      #print "Its an array with Name - ",matchObjDoubleArray.group(1)," and Size - ",matchObjFloatArray.group(2)
      doubleName = matchObjDoubleArray.group(1)
      doubleSize = matchObjDoubleArray.group(2)
    elif matchObjDoubleScalar:
      #print "Its a Scalar with Name ",matchObjDoubleScalar.group(1)
      doubleName = matchObjDoubleScalar.group(1)
      doubleSize = 1
    if matchObjDoubleScalarValue:
      #print "And Value ",matchObjDoubleScalarValue.group(1)
      doubleValue = matchObjDoubleScalarValue.group(1)
    pushVariables(doubleName,
                  doubleVarType,
                  doubleSize,
                  doubleValue)
  return None

def Transcendental(currentLine):
  "checks for transcendental functions in a line"
  matchObjLog  = re.findall('logf',currentLine, re.I)
  matchObjSin  = re.findall('sinf',currentLine, re.I)
  matchObjCos  = re.findall('cosf',currentLine, re.I)
  matchObjExp  = re.findall('expf',currentLine, re.I)
  matchObjSqrt = re.findall('sqrtf',currentLine, re.I)
  global TotalTranscendentals
  if matchObjLog:
    TotalTranscendentals = TotalTranscendentals + len(matchObjLog)  
  if matchObjSin:
    TotalTranscendentals = TotalTranscendentals + len(matchObjSin)  
  if matchObjCos:
    TotalTranscendentals = TotalTranscendentals + len(matchObjCos)  
  if matchObjExp:
    TotalTranscendentals = TotalTranscendentals + len(matchObjExp)  
  if matchObjSqrt:
    TotalTranscendentals = TotalTranscendentals + len(matchObjSqrt)  
  return None


def checkStartEndScope(currentline):
  "Checks for { and } to identify scope of a variable"
  matchStart  = re.search('{',currentLine, re.I)
  matchEnd    = re.search('}',currentLine, re.I)
  if matchStart:
    matchFor    = re.search('for',currentLine, re.I)
    matchWhile  = re.search('while',currentLine, re.I)
    matchIf     = re.search('if',currentLine, re.I)

    matchForPrev    = re.search('for',  previousLine, re.I)
    matchWhilePrev  = re.search('while',previousLine, re.I)
    matchIfPrev     = re.search('if',   previousLine, re.I)
    if matchFor or matchWhile or matchIf or matchForPrev or matchWhilePrev or matchIfPrev:
      scopeInitializer = ""
      if matchFor or matchForPrev:
	scopeInitializer = "For"
      elif matchWhile or matchWhilePrev:
	scopeInitializer = "While"
      elif matchIf or matchIfPrev:
	scopeInitializer = "if"
      scope.push(scopeInitializer)
    else:
      raise RuntimeError('Found a start of scope but was not able to find scope initializer')
  elif matchEnd:
    scope.pop()
  return
 
def GlobalMemoryTransaction(currentLine):
  "Collects data to estimate the number of global memory transaction of each warp"
  matches = re.findall('\[(.*?)\]',currentLine)
  #Sample Output
  #>>> re.findall('\[(.*?)\]',currentLine)
  #['i', 'i+4', 'B[i']
  for access in matches:
    offsets = re.findall('\+',access)
    indirect = re.findall('\w+\[',access)
    global NumOffsetAccesses
    global NumIndirectAccesses
    NumOffsetAccesses = NumOffsetAccesses + len(offsets)   
    NumIndirectAccesses = NumIndirectAccesses + len(indirect)
  return False

def MemoryOperations(currentLine):
  "Check for memory access in currentline"
  #TODO FIXME !!This wont work!! 
  #Does not detect A[B[i]]!! Instead, use this detect number of [, number of ] and if = [resent. Store would be one, loads would be (number([)-1)/2. Keep a check Number([) = Number(])
  #storeOperations = re.findall('\w+\[.*\].*\=',currentLine, re.I)
  storeOperations = re.findall('\[.*=',currentLine, re.I)
  #loadOperations = re.findall('\=.*\w+\[.*\]',currentLine, re.I)
  loadOperations = re.findall('\[',currentLine, re.I)
  global NumLoadOperations
  global NumStoreOperations
  NumStoreOperations = NumStoreOperations + len(storeOperations)
  NumLoadOperations  = NumLoadOperations + len(loadOperations) - len(storeOperations)
  if len(loadOperations) > 0 or len(storeOperations) > 0:
    GlobalMemoryTransaction(currentLine)
  return False

def ArithmeticInstructions(currentLine):
  "Checks for number of arithmetic operations in a line"
  #Right now A[i+4] is also included, need to take care of this!!!! TODO FIXME
  #print currentLine
  numArithmetic  = re.findall('\+\+|\+|\-|\*|/|\<\=|\>\=|\<\<|\>\>|\=\=|\<|\>',currentLine, re.I)
  global TotalArithmeticInstructions
  #print len(numArithmetic)
  TotalArithmeticInstructions = TotalArithmeticInstructions + len(numArithmetic)
  numArithmetic  = re.findall('\w+\[.*\+.*\]',currentLine, re.I)
  TotalArithmeticInstructions = TotalArithmeticInstructions - len(numArithmetic)
  return False

def FPDivMult(currentLine):
  "Checks for Floating Point Multiplication and Division"
  return False
###################################Function and Class Definition Ends Here################################################################

print "**************************************************************************"
print "****			Static Code Analyzer			      ****"
print "**************************************************************************"
print "****		   Please Use Python 2.7 or later		      ****"
print "**************************************************************************"
try:
  parser = argparse.ArgumentParser(description='Reads inputs to Static Serial Code Analyzer')
  parser.add_argument('-file',required=True, dest='file_name',help='file that you want analyzed')
  args = parser.parse_args()
  fileHandler = open(args.file_name, "r")
except IOError:
  print "There was an error reading ", args.file_name
  sys.exit()

for currentLine in fileHandler:
  #printFileLine(currentLine)
  checkStartEndScope(currentLine)
  #Call get variables after scope to detect scenarios like for(int i...)
  getVariables(currentLine)
  isStartOfAnnotation(currentLine)
  if StartAnalyzing :
    Transcendental(currentLine)
    ArithmeticInstructions(currentLine)
    MemoryOperations(currentLine)
  
  if isEndOfAnnotation(currentLine) :
    global StartAnalyzing
    StartAnalyzing = False
    break
  previousLine = currentLine

print "######################################################"
printVariables()
print "\n"
print "TotalTranscendentals -",TotalTranscendentals
print "TotalArithmeticInstructions -",TotalArithmeticInstructions
print "NumLoadOperations -",NumLoadOperations
print "NumStoreOperations -",NumStoreOperations
print "NumOffsetAccesses - ", NumOffsetAccesses 
print "NumIndirectAccesses - ", NumIndirectAccesses
print "\n"
print "######################################################"
