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
FoundFLPMulDiv = False
ControlDensity = "L"
WarpDivergenceRatio = 0 
MultiplicationFactorFor = 1 #Useful for scenarios where for loop is executed by thread body
MultiplicationFactorIf = 1 #Useful for scenarios where if is taken, different from for as multiplication factor would depend on bratio and we need a multiplication factor proportional to 1/32
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
  
  def getVarType(self):
    return self.varType

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

MultiplicationFactorFor = Stack()
MultiplicationFactorFor.push(1)

MultiplicationFactorIf = Stack()
MultiplicationFactorIf.push(1)

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

def Transcendental(currentLine, MultiplicationFactorFor,MultiplicationFactorIf):
  "checks for transcendental functions in a line"
  matchObjLog  = re.findall('logf',currentLine, re.I)
  matchObjSin  = re.findall('sinf',currentLine, re.I)
  matchObjCos  = re.findall('cosf',currentLine, re.I)
  matchObjExp  = re.findall('expf',currentLine, re.I)
  matchObjSqrt = re.findall('sqrtf',currentLine, re.I)
  global TotalTranscendentals
  if matchObjLog:
    TotalTranscendentals = TotalTranscendentals + len(matchObjLog)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  if matchObjSin:
    TotalTranscendentals = TotalTranscendentals + len(matchObjSin)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  if matchObjCos:
    TotalTranscendentals = TotalTranscendentals + len(matchObjCos)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  if matchObjExp:
    TotalTranscendentals = TotalTranscendentals + len(matchObjExp)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()  
  if matchObjSqrt:
    TotalTranscendentals = TotalTranscendentals + len(matchObjSqrt)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  return None


def checkStartEndScope(currentline):
  "Checks for { and } to identify scope of a variable"
  matchStart  = re.search('{',currentLine, re.I)
  matchEnd    = re.search('}',currentLine, re.I)
  global StartAnalyzing
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
      if matchEnd == None: #for scenarios like struct {}, scope ends in same line
        raise RuntimeError('Found a start of scope but was not able to find scope initializer')
      else:
        scope.push("struct/class")
  elif matchEnd: #for scenarios like struct {}, scope ends in same line
    if StartAnalyzing:
      if scope.front() == "if":
        MultiplicationFactorIf.pop()
      elif scope.front() == "for":
        MultiplicationFactorFor.pop()
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

def MemoryOperations(currentLine,MultiplicationFactorFor,MultiplicationFactorIf):
  "Check for memory access in currentline"
  #Below commented method do not work as -
  #Does not detect A[B[i]]!! Instead, use this detect number of [, number of ] and if = [resent. Store would be one, loads would be (number([)-1)/2. Keep a check Number([) = Number(])
  #Non commented ones are these new implementation
  #storeOperations = re.findall('\w+\[.*\].*\=',currentLine, re.I)
  storeOperations = re.findall('\[.*=',currentLine, re.I)
  #loadOperations = re.findall('\=.*\w+\[.*\]',currentLine, re.I)
  loadOperations = re.findall('\[',currentLine, re.I)
  global NumLoadOperations
  global NumStoreOperations
  NumStoreOperations = NumStoreOperations + len(storeOperations)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  NumLoadOperations  = NumLoadOperations + len(loadOperations) - len(storeOperations)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  if len(loadOperations) > 0 or len(storeOperations) > 0:
    GlobalMemoryTransaction(currentLine)
  return False

def ArithmeticInstructions(currentLine,MultiplicationFactorFor,MultiplicationFactorIf):
  "Checks for number of arithmetic operations in a line"
  #Right now A[i+4] is also included, need to take care of this!!!! TODO FIXME
  #print currentLine
  numArithmetic  = re.findall('\+\+|\+|\-|\*|/|\<\=|\>\=|\<\<|\>\>|\=\=|\<|\>',currentLine, re.I)
  global TotalArithmeticInstructions
  #print len(numArithmetic)
  TotalArithmeticInstructions = TotalArithmeticInstructions + len(numArithmetic)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  numArithmetic  = re.findall('\w+\[.*\+.*\]',currentLine, re.I)
  TotalArithmeticInstructions = TotalArithmeticInstructions - len(numArithmetic)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  return False

def FPDivMult(currentLine):
  "Checks for Floating Point Multiplication and Division"
  matches = re.finditer("\*",currentLine)
  startFrom=0
  equalto = re.finditer("=",currentLine)
  print equalto
  for iterE in equalto:
    (startFrom,nouse) = iterE.span()
    startFrom = startFrom+1
    break

  for match in matches:
    print "####"
    (start,end) = match.span()
    print start, " ",currentLine[start]
    print end, " ",currentLine[end]
    operandA = 1; #1 - Scalar, 2 - Array, 3 - Constant
    operandB = 1;
    start = start - 1 #start is the position of *
    print start, " ",currentLine[start]
    while (currentLine[start] == " "):
      start=start-1
    if (currentLine[start] == ")"):
      start=start-1
      startFrom = start
      while(currentLine[startFrom] != "("):
        startFrom = startFrom-1
    if (currentLine[start] == "]"):
      operandA = 2
      while (currentLine[start] != "["):
	start=start-1  
      start=start-1 #Just Reached [, need to decrement 
    print currentLine[startFrom:start+1]
    temp = re.search('[\( *=\/\+](\w.*)$',currentLine[startFrom:start+1])
    if temp:
      print "match"
      print temp.group(1) 
      if temp.group(1) in variables:
        if variables[temp.group(1)].getVarType() == 1 :
	  global FoundFLPMulDiv
          FoundFLPMulDiv = True
      elif re.search('\df',temp.group(1)):
	global FoundFLPMulDiv
        FoundFLPMulDiv = True
    else:
      operandA=3 #If no variable found, then its a constant
    startFrom = end 
    print currentLine[startFrom:]
    temp = re.search('(\w.*?)[ +*/\[\)]',currentLine[startFrom:])
    if temp:
      print "match"
      print temp.group(1)
      if temp.group(1) in variables:
        if variables[temp.group(1)].getVarType() == 1 :
	  global FoundFLPMulDiv
          FoundFLPMulDiv = True
      elif re.search('\df',temp.group(1)):
	global FoundFLPMulDiv
        FoundFLPMulDiv = True
      (p,tempStartFrom) = temp.span()
      startFrom = startFrom+tempStartFrom-1
      print startFrom, " ",currentLine[startFrom]
      if (currentLine[startFrom] == "["):
	operandB=2
	while(currentLine[startFrom] != "]"):
	  startFrom=startFrom+1
	startFrom=startFrom+1 #You just reached ], increment by 1
	print startFrom
    else:
      operandB=3 #If no match found, then a constant
  return False

def checkControlDensity(currentLine):
  "Checks for if/while/do statements"
  ifCheck = re.findall('\Wif\W', currentLine)
  whileCheck = re.findall('\Wwhile\W', currentLine)
  forCheck = re.findall('\Wfor\W', currentLine)
  if len(ifCheck)>0 or len(whileCheck)>0 or len(forCheck)>0 :
    global ControlDensity
    ControlDensity = "H"
  return False

def checkWarpDivergence(currentLine):
  "Checks for Warp Divergence"
  ratios = re.findall('BRATIO\d+\.\d+?',currentLine)
  bratio = 0
  for ratio in ratios:
    value = re.findall('\d+\.\d+',ratio)
    #print ratio
    #print value
    bratio = bratio*float(value[0])
  if (bratio > WarpDivergenceRatio):
    global WarpDivergenceRatio
    WarpDivergenceRatio = bratio
  MultiplicationFactorIf.push(bratio)
  return

def checkForMultFactor(currentLine):
  "Checks Multiplicative factor of For Loop within a thread body"
  ratios = re.findall('FRATIO\d+?',currentLine)
  fratio = 0
  for ratio in ratios:
    value = re.findall('\d+',ratio)
    #print ratio
    #print value
    fratio = fratio*int(value[0])
  MultiplicationFactorFor.push(fratio)
  return

###################################Function and Class Definition Ends Here################################################################

print "**************************************************************************"
print "****			C Code Parser   			      ****"
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
  printFileLine(currentLine)
  checkStartEndScope(currentLine)
  #Call get variables after scope to detect scenarios like for(int i...)
  getVariables(currentLine)
  isStartOfAnnotation(currentLine)
  if StartAnalyzing :
    Transcendental(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    ArithmeticInstructions(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    MemoryOperations(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    FPDivMult(currentLine)
    checkControlDensity(currentLine)
    checkWarpDivergence(currentLine)
    checkForMultFactor(currentLine)
  
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
if (TotalTranscendentals==0):
  print "Transcendental Ratio - L"
elif ( TotalTranscendentals/(TotalArithmeticInstructions+NumLoadOperations+NumStoreOperations) < 0.15):
  print "Transcendental Ratio - M"
else:
  print "Transcendental Ratio - H"

if (NumOffsetAccesses>0 or NumIndirectAccesses>0):
  print "Global Memory Operation - L"
else:
  print "Global Memory Operation - H"

if (TotalArithmeticInstructions+TotalTranscendentals+NumLoadOperations+NumStoreOperations < 70):
  print "Total Instruction - L"
else:
  print "Total Instruction - H"

if (TotalArithmeticInstructions < NumLoadOperations+NumStoreOperations):
  print "Arithmetic Intensity - L"
elif ((TotalArithmeticInstructions/(NumLoadOperations+NumStoreOperations))>1 and (TotalArithmeticInstructions/(NumLoadOperations+NumStoreOperations))<5 ):
  print "Arithmetic Intensity - M"
else:
  print "Arithmetic Intensity - H"

if (FoundFLPMulDiv):
  print "Floating Point Mul/Div - H" 
else:
  print "Floating Point Mul/Div - L" 

print "ControlDensity - ",ControlDensity

if (WarpDivergenceRatio >=0 and WarpDivergenceRatio <=1):
  print "BranchDivergence - L"
else:
  print "BranchDivergence - H"
