#!/usr/bin/python
import sys
import re
import argparse
import os
import pseudoAST

variables = dict()
TotalTranscendentals = 0
TotalArithmeticInstructions = 0
StartAnalyzing = False
previousLine = ""
NumLoadOperations = 0
NumStoreOperations = 0
NumOffsetAccesses = 0
NumDoubleAccesses = 0
NumIndirectAccesses = 0 #A[B[i]]
FoundFLPMulDiv = False
ControlDensity = "L"
WarpDivergenceRatio = 0 
MultiplicationFactorFor = 1 #Useful for scenarios where for loop is executed by thread body
MultiplicationFactorIf = 1 #Useful for scenarios where if is taken, different from for as multiplication factor would depend on bratio and we need a multiplication factor proportional to 1/32
Warnings=[]
WarningsCounter=1
PerLineVarInAnnotatedRegion = []
nThreadsCount = 1;
instCountWithFRatio = 0;
fratioIndex = 999999;
NumStoreOperationsThisLine = 0;
NumLoadOperationsThisLine = 0;
CriticalPath= 0;
###################################Function and Class Definition Starts Here################################################################
class VariableState():
  def __init__(self,name,scope,varType,size,value,iteratorVar):
    self.name = name
    self.scope = scope
    self.varType = varType #0 - Int, 1 - Float, 2 - Double
    self.size = size
    self.value = value
    self.iteratorVar = iteratorVar
    return None
  
  def printValues(self):
    print "The values of this entry are"
    print "Name                 - ",self.name
    print "Scope                - ",self.scope
    print "varType              - ",self.varType
    print "size                 - ",self.size
    print "value                - ",self.value
    print "iteratorVar          - ",self.iteratorVar
    return None
  
  def getVarType(self):
    return self.varType
  
  def getValue(self):
    return self.value
  
  def getIteratorVar(self):
    return self.iteratorVar


class Stack():
  def __init__(self,name):
    self.name = name
    self.items = []
    self.countStack = []
    self.Count = 0
    
  def isEmpty(self):
    return self.items == []
    
  def push(self, item):
    self.Count = self.Count+1
    self.countStack.append(self.Count)
    print self.name+" - pushing "+str(item)
    return self.items.append(item)

  def push_same(self,item):
    return self.items.append(item)

  def pop_temp(self):
    return self.items.pop()
  
  def pop(self):
    self.countStack.pop()
    self.Count = self.Count-1
    return self.items.pop()
  
  def getElements(self):
    return self.items

  def front(self):
    Obj = self.pop_temp()
    self.push_same(Obj)
    return Obj

  def frontId(self):
    index = self.countStack.pop()
    self.countStack.append(index)
    return index

  def len(self):
    return len(self.items)

class VarInEachLine():
  def __init__(self,lhs,rhs,forCount,scope,ifCount,cyclesToExecute,scopeId,currentLine):
    self.lhs = lhs;
    self.rhs = rhs;
    self.forCount = forCount;
    self.ifCount  = ifCount
    self.scope = scope;
    self.cycles = cyclesToExecute
    self.scopeId = scopeId
    self.currentLine = currentLine
    print "Inserting - "+currentLine
  
  def printVariables(self):
    l = ""
    for i in self.lhs:
    	l=l+" "+i;
    r= ""
    for i in self.rhs:
    	r=r+" "+i;
    print "LHS - "+l
    print "RHS - "+r
    print "For Ratio - "+str(self.forCount)
    print "If  Ratio - "+str(self.ifCount)
    print "Scope     - "+str(self.scope)
    print "ScopeId   - "+str(self.scopeId)
    print "Cycles    - "+str(self.cycles)
    print "Line	     - "+str(self.currentLine)
  
  def getCycles(self):
    return self.cycles
  def setLhs(self,lhsIn):
    self.lhs = lhsIn
  
  def setLhs(self,rhsIn):
    self.rhs = rhsIn
  
  def ifInLhs(self,var):
    if var in self.lhs:
    	return True
    else:
  	return False
 
  def returnFor(self):
    return self.forCount
 
  def returnIf(self):
    return self.ifCount

  def isFor(self):
    return (self.forCount	> 1)
  
  def getScope(self):
    return self.scope

  def getLine(self):
    return self.currentLine
  
  def getScopeId(self):
    return self.scopeId
  
  def getLHS(self):
    return self.lhs
  
  def checkLHS(self,lhs):
    for i in self.rhs:
      if i in lhs:
	return True
    return False

scope = Stack('scope') #Accessed to understand the scope of a variable
scope.push('Global')

MultiplicationFactorFor = Stack('For count stack')
MultiplicationFactorFor.push(1)

MultiplicationFactorIf = Stack('If ratio stack')
MultiplicationFactorIf.push(1)

def printVariables():
    print "**********"
    for key in variables:
      variables[key].printValues()
      print "**********"
    return True

def printPerLineVariables():
	"Prints the contents of PerLineVarInAnnotatedRegion list"
	print "***********"
	lineNum = 1
	for line in PerLineVarInAnnotatedRegion:
		print "Line "+str(lineNum)
		line.printVariables()
		lineNum = lineNum+1
		print "***"

	print "***********"
	return

def pushVariables(name,
		  varType,
		  size,
		  value):
  #name - Name of the variable, varType - int/float/double, size - scalar has size 1, array has size > 1, value - for a scalar, value if assigned, else None
  #varType 0 - Int, 1 - Float, 2 - Double, 3 - Pointer
  "This function pushes the variables and its associated properties to dictionary variables"
  iteratorVar = False
  if (scope.front() == "For"):
    if (StartAnalyzing == True):
      iteratorVar = True #TODO FIXME - This is still not accurate, need to verify this!
  variables[name] = VariableState(name,scope.front(),varType,size,value, iteratorVar)
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
    matchObjFloatArray2       = re.search('float \*(\w+)',currentLine, re.I)
    matchObjFloatScalar      = re.search('float (\w+)',currentLine, re.I)
    matchObjFloatScalarValue = re.search('=\D*(\d+)',currentLine, re.I)
    floatName = ""
    floatVarType = 1
    floatSize = 0
    floatValue = None
    if matchObjFloatArray:
      #print "Its an array with Name - ",matchObjFloatArray.group(1)," and Size - ",matchObjFloatArray.group(2)
      floatName = matchObjFloatArray.group(1)
      floatSize = matchObjFloatArray.group(2)
    if matchObjFloatArray2:
      #print "Its an array with Name - ",matchObjFloatArray.group(1)," and Size - ",matchObjFloatArray.group(2)
      floatName = matchObjFloatArray2.group(1)
      floatSize = 3
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
    doubleVarType = 2
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
    matchElse     = re.search('else',currentLine, re.I)
    matchStruct     = re.search('struct',   currentLine, re.I)
    matchDo     = re.search('do',   currentLine, re.I)

    matchForPrev    = re.search('for',  previousLine, re.I)
    matchWhilePrev  = re.search('while',previousLine, re.I)
    matchIfPrev     = re.search('if',   previousLine, re.I)
    matchElsePrev     = re.search('Else',   previousLine, re.I)
    matchStructPrev     = re.search('struct',   previousLine, re.I)
    matchDoPrev     = re.search('do',   previousLine, re.I)
    pushToForMultStack = False #Useful when for is outside the annotation region and fratio is not there, we push to scope but not multforstack. So when popping, lead to zero entries in latter
    if matchFor or matchWhile or matchIf or matchForPrev or matchWhilePrev or matchIfPrev or matchStruct or matchStructPrev or matchDo or matchDoPrev or matchElse or matchElsePrev:
      scopeInitializer = ""
      if matchFor or matchForPrev:
	scopeInitializer = "For"
	ratios = re.findall('FRATIO\d+',currentLine)
	if (ratios):
	  pushToForMultStack = False
	else:
	  pushToForMultStack = True
      elif matchWhile or matchWhilePrev:
	scopeInitializer = "While"
      elif matchIf or matchIfPrev or matchElsePrev or matchElse:
	scopeInitializer = "if"
      elif matchStruct or matchStructPrev:
        scopeInitializer = "struct"
      elif matchDo or matchDoPrev:
        scopeInitializer = "do"
      scope.push(scopeInitializer)
      if(pushToForMultStack):
	MultiplicationFactorFor.push(1)
	
    else:
      if matchEnd == None: #for scenarios like struct {}, scope ends in same line
        raise RuntimeError('Found a start of scope but was not able to find scope initializer')
      else:
        scope.push("struct/class")
  elif matchEnd: #for scenarios like struct {}, scope ends in same line
    if StartAnalyzing:
      if scope.front() == "if":
        MultiplicationFactorIf.pop()
	print "Scope Found if, popping, New Length "+str((MultiplicationFactorIf.len()))
      elif scope.front() == "For":
        MultiplicationFactorFor.pop()
	print "Scope Found For, popping, New Length "+str((MultiplicationFactorFor.len()))
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
    #NumOffsetAccesses = NumOffsetAccesses + len(offsets)   #access has list of all memory transactions, if a + is there in it, increment offset accesses
    if (offsets):
      GlobalOffsetTransaction(access,currentLine)
    NumIndirectAccesses = NumIndirectAccesses + len(indirect)
    if (indirect):
      GenerateIndirectWarning(access,currentLine)
  return False

def GlobalOffsetTransaction(access,currentLine):
  "Checks the offset for A[i+c] sort of memory transactions"
  global NumOffsetAccesses
  offsets = re.findall('\+(.*)',access)
  print "offset pattern is"
  print access
  print "and extracted value is"
  print offsets
  if(offsets):
    print "Offset is"
    print offsets[0].strip()
    if(re.match('\d+',offsets[0].strip())):
      try:
	if (int(offsets[0].strip()) <= 4):
	  print "Offset is a int with number <=2"
	else:
	  print "Offset is quite huge! Constant > 4!"
	  NumOffsetAccesses=NumOffsetAccesses+1
      except:
	print str(WarningsCounter)+". Offset seems to be a variable hard to determine! Not marking it as irregular access/access generating many transactions! PLEASE VERIFY!---- "+currentLine.strip()+"\n"
	Warnings.append(str(WarningsCounter)+". Offset seems to be a variable hard to determine! Not marking it as irregular access/access generating many transactions! PLEASE VERIFY!---- "+currentLine.strip()+"\n")
	global WarningsCounter
        WarningsCounter=WarningsCounter+1
    else: #Offset is not an integer, need to check if variable exists
      if offsets[0].strip() in variables:
	value = variables[offsets[0].strip()].getValue()
	iterVar = variables[offsets[0].strip()].getIteratorVar()
	if (value == None):
	  Warnings.append(str(WarningsCounter)+". Check Out "+access.strip()+" in line "+currentLine.strip()+"\n")
	  global WarningsCounter
	  WarningsCounter=WarningsCounter+1
	else:
	  if (value > 4 and iterVar==False):
	    print "Offset is quite huge! Value > 4! Value is "+value
            NumOffsetAccesses=NumOffsetAccesses+1
      else:	
	print str(WarningsCounter)+". Offset seems to be a variable hard to determine! Not marking it as irregular access/access generating many transactions! PLEASE VERIFY!---- "+currentLine.strip()+"\n"
	Warnings.append(str(WarningsCounter)+". Offset seems to be a variable hard to determine! Not marking it as irregular access/access generating many transactions! PLEASE VERIFY!---- "+currentLine.strip()+"\n")
	global WarningsCounter
        WarningsCounter=WarningsCounter+1
  return False

def GenerateIndirectWarning(access,currentLine):
  "Generates warning for indirect access"
  print "Indirect Warning"
  Warnings.append(str(WarningsCounter)+". Memory Coalescing Warning - ***"+access.strip()+"]*** is an indirect access in line "+currentLine.strip()+"\n")
  global WarningsCounter
  WarningsCounter=WarningsCounter+1

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
  NumLoadOperations  = NumLoadOperations + len(loadOperations) *MultiplicationFactorFor.front()*MultiplicationFactorIf.front() - len(storeOperations)*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  global NumStoreOperationsThisLine
  global NumLoadOperationsThisLine
  NumStoreOperationsThisLine = len(storeOperations)
  NumLoadOperationsThisLine =  len(loadOperations) - len(storeOperations)
  if len(loadOperations) > 0 or len(storeOperations) > 0:
    GlobalMemoryTransaction(currentLine)
    doubleMem(currentLine)
  return False

def ArithmeticInstructions(currentLine,MultiplicationFactorFor,MultiplicationFactorIf):
  "Checks for number of arithmetic operations in a line"
  numArithmetic  = re.findall('\+\+|\+|\-|\*|/|<=|\>=|<<|>>|==|<|>|&&',currentLine, re.I)
  print numArithmetic
  numFalseArithmetic  = re.findall('//',currentLine, re.I) #// interpreted as 2 divisions
  print numFalseArithmetic
  global TotalArithmeticInstructions
  print len(numArithmetic) - 2*len(numFalseArithmetic) #2 as // is interpreted as 2 operations
  TotalArithmeticInstructions = TotalArithmeticInstructions + (len(numArithmetic) -2*len(numFalseArithmetic))*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  print "TotalArithmeticInstructions ", TotalArithmeticInstructions
  #numArithmetic  = re.findall('\w+\[.*?\+.*?\]',currentLine, re.I) 
  numArithmetic  = re.findall('\w+\[[^=]*?\+.*?\]',currentLine, re.I) 
  print len(numArithmetic)
  for matches in numArithmetic: 
  #Required as for example in line - new_dw = ((ETA * delta[j] * ly[k]) + (MOMENTUM * oldw[k][j]));
  #delta[j] * ly[k]) + (MOMENTUM * oldw[k] identified as mem[A+B] pattern while delta[j] * ly[k] identified as mem[A*B] pattern. Even after no greedy search. Difficult to come up with patterns that identify mem[A*B[i]*k] and dont give issues like above. Also filtering out adds from mem[A+B] is important. As a result 2 would be subtracted and number of arithmetic instructions in this would become 2
    if(re.findall('\].*?\[',matches)):
      numArithmetic.remove(matches)
  TotalArithmeticInstructions = TotalArithmeticInstructions - (len(numArithmetic))*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  #numArithmetic  = re.findall('\w+\[.*?\*.*?\]',currentLine, re.I)
  numArithmetic  = re.findall('\w+\[[^=]*?\*.*?\]',currentLine, re.I)
  print len(numArithmetic)
  for matches in numArithmetic: 
    if(re.findall('\].*?\[',matches)):
      numArithmetic.remove(matches)
  TotalArithmeticInstructions = TotalArithmeticInstructions - (len(numArithmetic))*MultiplicationFactorFor.front()*MultiplicationFactorIf.front()
  print "TotalArithmeticInstructions ",TotalArithmeticInstructions
  return False

def FPDivMult(currentLine):
  "Checks for Floating Point Multiplication and Division"
  matches = re.finditer("\*",currentLine)
  startFrom=0
  equalto = re.finditer("=",currentLine)
  #print equalto
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

def FPDiv(currentLine):
  "Checks for Floating Point Multiplication and Division"
  matches = re.finditer("/",currentLine)
  startFrom=0
  equalto = re.finditer("=",currentLine)
  #print equalto
  for iterE in equalto:
    (startFrom,nouse) = iterE.span()
    startFrom = startFrom+1
    break

  for match in matches:
    print "Division Found"
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
    temp = re.search('[( *=/+](\w.*)$',currentLine[startFrom:start+1].strip())
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

def doubleMem(currentLine):
  "Checks Load to a double variable"
  storeOperations = re.finditer('\[.*=',currentLine, re.I)
  print "Checking double store operation"
  startFrom = 0
  for store in storeOperations:
    (start,end) = store.span()
    print start, " ",currentLine[start]
    operandA = 1; #1 - Scalar, 2 - Float, 3 - Double
    start = start - 1 #start is the position of [
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
    #temp = re.search('[(\s*=/+](\w.*)$',currentLine[startFrom:start+1].strip())
    temp = re.search('[(\s*=/+](\w.*)$',currentLine[startFrom:start+1])
    #temp = currentLine[startFrom:start+1] #For store, all the above hoops may not be true
    if temp:
      print "match"
      print temp.group(1)
      if temp.group(1) in variables:
	print "Found variable in List!"
        if variables[temp.group(1)].getVarType() == 2 :
	  global NumDoubleAccesses
          NumDoubleAccesses = NumDoubleAccesses+1
  print "Checking double store operation - Done"
  return False

def checkControlDensity(currentLine):
  "Checks for if/while/do statements"
  ifCheck = re.findall('\Wif\W', currentLine)
  whileCheck = re.findall('\Wwhile\W', currentLine)
  #forCheck = re.findall('\Wfor\W', currentLine)
  #if len(ifCheck)>0 or len(whileCheck)>0 or len(forCheck)>0 :
  if len(ifCheck)>0 or len(whileCheck)>0 : #Removing For as Annotation Starts above For
    global ControlDensity
    ControlDensity = "H"
    print "Found Control Density"
  return False

def checkWarpDivergence(currentLine):
  "Checks for Warp Divergence"
  ratios = re.findall('BRATIO\d+\.\d+',currentLine)
  bratio = 1
  for ratio in ratios:
    value = re.findall('\d+\.\d+',ratio)
    #print ratio
    print value
    bratio = bratio*float(value[0])
  if (ratios):
    print "Bratio found"
    tempBratio=bratio*32 #To see how many warps diverge
    if (32-tempBratio<bratio*32):
      tempBratio = 32-tempBratio
    #tempBratio = tempBratio*MultiplicationFactorFor.front()
    print "temp bratio is ",str(tempBratio)
    if (tempBratio > WarpDivergenceRatio):
      global WarpDivergenceRatio
      WarpDivergenceRatio = tempBratio
      print "Divergence ratio is ",str(WarpDivergenceRatio)
    else:
      print "Divergence ratio using old ",str(WarpDivergenceRatio)
  if (ratios):
    MultiplicationFactorIf.push(bratio)
  return

def checkForMultFactor(currentLine):
  "Checks Multiplicative factor of For Loop within a thread body"
  ratios = re.findall('FRATIO\d+',currentLine)
  fratio = 1
  for ratio in ratios:
    value = re.findall('\d+',ratio)
    print ratio
    #print value
    fratio = fratio*int(value[0])
    MultiplicationFactorFor.push(fratio)
  return

def nthreads(currentLine):
  "Checks Multiplicative factor of For Loop within a thread body"
  ratios = re.findall('NTRATIO\d+',currentLine)
  print ratios
  for ratio in ratios:
    value = re.findall('\d+',ratio)
    print value
    global nThreadsCount
    nThreadsCount = nThreadsCount*int(value[0]) 
  return

def checkKernelSize(currentLine):
  
  return

def extractEveryVariable(currentLine):
	"Extract all input and output variable from the line"
	if re.findall("Annotation.*Begins",currentLine):
		return
	if re.findall("Annotation.*Ends",currentLine):
		return
	cyclesToExecute = pseudoAST.generateAST(currentLine)
	rhsVar = []
	lhsVar = []
	currentLineStripped = currentLine.strip()
	possibleComment = re.match('^//',currentLineStripped)
	if(possibleComment):
		print "This line is a comment"
		return
	#Strip comments at the end of a line
	trailComments = re.findall('//.*',currentLineStripped)
	print "extractEveryVariable"
	if (trailComments):
		currentLineStripped = currentLineStripped.replace(trailComments[0],"")

	#remove initializations like "int", "float" etc
	currentLineStripped = re.sub(r'\bint\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bfloat\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bdouble\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bif\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bNTRATIO\d+\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bFRATIO\d+\b',"",currentLineStripped)
	currentLineStripped = re.sub(r'\bBRATIO\d+\.\d+\b',"",currentLineStripped)
	#currentLineStripped = re.sub(r'\bfor\b',"",currentLineStripped) #Need for, for will only have one variable that is extracted
	#get lhs and rhs position
	lhsEnd=0
	rhsStart=0
	lhs = ""
	rhs = ""
	for match in re.finditer("[\w\d\s]=[\s\d\w]",currentLineStripped):
		lhsEnd,rhsStart = match.span()
		break
	if (rhsStart==0):
		lhs = ""
		rhs = currentLineStripped
	else:
		lhs = currentLineStripped[0:lhsEnd+1]
		rhs = currentLineStripped[rhsStart:]
	
	lhs = (re.sub('[^a-zA-Z]', ' ',lhs)).strip()
	rhs = (re.sub('[^a-zA-Z]', ' ',rhs)).strip()
	
	#get lhs elements
	lhsVar = lhs.split()	
	rhsVar = rhs.split()
	if (len(lhsVar)==0 and len(rhsVar)==0):
		return
	reqLHSLength = 1
	if "for" in lhsVar:
	  reqLHSLength = 2
	if len(lhsVar) > reqLHSLength:
	  while len(lhsVar) != reqLHSLength:
	      if lhsVar[len(lhsVar)-1] in rhsVar:
		lhsVar.remove(lhsVar[len(lhsVar)-1])
	      else:
		rhsVar.append(lhsVar[len(lhsVar)-1])
		lhsVar.remove(lhsVar[len(lhsVar)-1])
	PerLineVarInAnnotatedRegion.append(VarInEachLine(lhsVar,rhsVar,MultiplicationFactorFor.front(),scope.front(),MultiplicationFactorIf.front(),int(cyclesToExecute),scope.frontId(),currentLine.strip()))
	return 

def instCountForInnerFor(currentLine):
  "Trip count for inner for loops in case the total instruction count > threshold"
  ratios = re.findall('FRATIO\d+',currentLine)
  global fratioIndex
  global instCountWithFRatio
  if (ratios):
    fratioIndex = scope.frontId()
  if fratioIndex <= scope.frontId():
    #scope is a stack structure, the index increments by 1 when you insert something and decrements hen pop. All if/while/for under for marked with fratio will have index > fratio marked for 
    numArithmetic  = re.findall('\+\+|\+|\-|\*|/|<=|\>=|<<|>>|==|<|>',currentLine, re.I)
    numFalseArithmetic  = re.findall('//',currentLine, re.I) #// interpreted as 2 divisions
    instCountWithFRatio =  instCountWithFRatio + (len(numArithmetic) -len(numFalseArithmetic))
    numArithmetic  = re.findall('\w+\[[^=]*?\+.*?\]',currentLine, re.I)
    for matches in numArithmetic:
      if(re.findall('\].*?\[',matches)):
	numArithmetic.remove(matches)
    instCountWithFRatio = instCountWithFRatio - (len(numArithmetic))
    numArithmetic  = re.findall('\w+\[[^=]*?\*.*?\]',currentLine, re.I)
    for matches in numArithmetic:
      if(re.findall('\].*?\[',matches)):
	numArithmetic.remove(matches)
    instCountWithFRatio = instCountWithFRatio - (len(numArithmetic))
    global NumLoadOperationsThisLine
    global NumStoreOperationsThisLine
    instCountWithFRatio = instCountWithFRatio + NumLoadOperationsThisLine + NumStoreOperationsThisLine
    print "Within Fratio"
    print instCountWithFRatio
  return


def instructionLevelParallelism():
  "Goes backwards to look at instruction level parallelism"
  print "ILP!!!"
  ReducedAnnotatedRegion = []
  flag = False
  i = 0
  while flag==False:
    if (bool(re.search("NTRATIO",PerLineVarInAnnotatedRegion[i].getLine()))==True):
      i=i+1
    else:
      flag=True
  scopeIdC = PerLineVarInAnnotatedRegion[i].getScopeId();
  IncomingList =[]
  OutgoingList =[]
  j=0
  while i<len(PerLineVarInAnnotatedRegion):
    #if (scopeIdC == PerLineVarInAnnotatedRegion[i].getScopeId()):
    if (1):
      ReducedAnnotatedRegion.append(PerLineVarInAnnotatedRegion[i])
      IncomingList.append([])
      OutgoingList.append([])
      if(j!=0):
	k = 0
	while (k < len(ReducedAnnotatedRegion)-1):
	  if(PerLineVarInAnnotatedRegion[i].checkLHS(ReducedAnnotatedRegion[k].getLHS())):
	    OutgoingList[k].append(j)
	    IncomingList[(len(ReducedAnnotatedRegion)-1)].append(k)
	  k=k+1
      j=j+1
    i=i+1
  print "******"
  Node0 = []
  for p in range(len(ReducedAnnotatedRegion)):
    print p
    print ReducedAnnotatedRegion[p].getLine()
    print IncomingList[p]
    print OutgoingList[p]
    print str(ReducedAnnotatedRegion[p].getCycles())
    print str(ReducedAnnotatedRegion[p].returnIf())
    print str(ReducedAnnotatedRegion[p].returnFor())
    if (IncomingList[p]==[]):
      Node0.append(p)
    print "\n"
  print "******"
  possibleCriticalPath = []
  print "Node 0's -"
  print Node0
  for dfsp in Node0:
    #Do DFS for dfsp
    myStack = Stack("DFS Stack")
    myStack.push(dfsp)
    visited = set()
    distance = [-999]*len(ReducedAnnotatedRegion)
    distance[dfsp] = ReducedAnnotatedRegion[dfsp].getCycles()*ReducedAnnotatedRegion[dfsp].returnIf()*ReducedAnnotatedRegion[dfsp].returnFor()
    while (myStack.isEmpty() == False):
      vertex = myStack.pop()
      print distance
      if vertex not in visited:
	visited.add(vertex)
        for pushi in OutgoingList[vertex]:
	  if pushi in visited:
	    continue
	  else:
	    myStack.push(pushi)
	    print "("+str(vertex)+","+str(distance[vertex])+")"
	    print "("+str(pushi)+","+str(ReducedAnnotatedRegion[pushi].getCycles()*ReducedAnnotatedRegion[pushi].returnIf()*ReducedAnnotatedRegion[pushi].returnFor())+")"
	    dist = int(distance[vertex]) + int(ReducedAnnotatedRegion[pushi].getCycles()*ReducedAnnotatedRegion[pushi].returnIf()*ReducedAnnotatedRegion[pushi].returnFor())
	    print dist
	    if (dist>distance[pushi]):
	      distance[pushi] = dist
	      print "Selected!"
    possibleCriticalPath.append(max(distance))
  print possibleCriticalPath
  global CriticalPath
  CriticalPath = max(possibleCriticalPath)
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
  print args.file_name
except IOError:
  print "There was an error reading ", args.file_name
  sys.exit()

for currentLine in fileHandler:
  printFileLine(currentLine)
  checkStartEndScope(currentLine)
  #Call get variables after scope to detect scenarios like for(int i...)
  getVariables(currentLine)
  isStartOfAnnotation(currentLine)
  nthreads(currentLine)
  if StartAnalyzing :
    checkForMultFactor(currentLine)
    Transcendental(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    ArithmeticInstructions(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    MemoryOperations(currentLine, MultiplicationFactorFor,MultiplicationFactorIf)
    FPDivMult(currentLine)
    FPDiv(currentLine)
    checkControlDensity(currentLine)
    #checkForMultFactor(currentLine)
    extractEveryVariable(currentLine)
    checkWarpDivergence(currentLine)
    instCountForInnerFor(currentLine)
  
  if isEndOfAnnotation(currentLine) :
    global StartAnalyzing
    StartAnalyzing = False
    break
  previousLine = currentLine
instructionLevelParallelism()
print "######################################################"
printVariables()
printPerLineVariables()
print "\n"
print "TotalTranscendentals -",TotalTranscendentals
print "TotalArithmeticInstructions -",TotalArithmeticInstructions
print "NumLoadOperations -",NumLoadOperations
print "NumStoreOperations -",NumStoreOperations
print "NumOffsetAccesses - ", NumOffsetAccesses 
print "NumIndirectAccesses - ", NumIndirectAccesses
print "NumDoubleAccesses - ", NumDoubleAccesses
print "CriticalPath - ", CriticalPath
print "nThreadsCount - ",nThreadsCount
print "instCountWithFRatio - ",instCountWithFRatio
if (len(Warnings)>0):
  print "Warnings!!!!"
  for i in Warnings:
    print i
print "\n"
print "######################################################"
basename = os.path.basename(args.file_name)
writeLine = os.path.splitext(basename)[0]
if (TotalTranscendentals==0):
  print "Transcendental Ratio - L"
  writeLine= writeLine+",L"
elif ( (TotalTranscendentals)/((float)(TotalArithmeticInstructions+NumLoadOperations+NumStoreOperations)) < 0.15):
  print "Transcendental Ratio - M" + str(TotalTranscendentals/((float)(TotalArithmeticInstructions+NumLoadOperations+NumStoreOperations)))
  writeLine= writeLine+",M"
else:
  print "Transcendental Ratio - H"
  writeLine= writeLine+",H"

if (TotalArithmeticInstructions < NumLoadOperations+NumStoreOperations):
  print "Arithmetic Intensity - L"
  writeLine= writeLine+",L"
elif ((TotalArithmeticInstructions/(NumLoadOperations+NumStoreOperations)) >=1 and (TotalArithmeticInstructions/(NumLoadOperations+NumStoreOperations))<5 ):
  print "Arithmetic Intensity - M"
  writeLine= writeLine+",M"
else:
  print "Arithmetic Intensity - H"
  writeLine= writeLine+",H"

if (NumOffsetAccesses>0 or NumIndirectAccesses>0 or NumDoubleAccesses>0):
  print "Global Memory Operation - L"
  writeLine= writeLine+",L"
else:
  print "Global Memory Operation - H"
  writeLine= writeLine+",H"

if (WarpDivergenceRatio >=0 and WarpDivergenceRatio <1):
  print "BranchDivergence - L"+" "+str(WarpDivergenceRatio)
  writeLine= writeLine+",L"
else:
  print "BranchDivergence - H"+" "+str(WarpDivergenceRatio)
  writeLine= writeLine+",H"

print "ControlDensity - ",ControlDensity
writeLine=writeLine+","+ControlDensity

if (FoundFLPMulDiv):
  print "Floating Point Mul/Div - H" 
  writeLine=writeLine+",H"
else:
  print "Floating Point Mul/Div - L" 
  writeLine=writeLine+",L"

if (TotalArithmeticInstructions+TotalTranscendentals+NumLoadOperations+NumStoreOperations < 70):
  print "Total Instruction - L"
  writeLine=writeLine+",L"
else:
  if (TotalArithmeticInstructions+TotalTranscendentals+NumLoadOperations+NumStoreOperations < 200):
    print "Total Instruction - H"
    writeLine=writeLine+",H"
  else:
    if (instCountWithFRatio < 70):
      print "Total Instruction - L"
      writeLine=writeLine+",L"
    else:
      print "Total Instruction - H"
      writeLine=writeLine+",H"
print "Num Threads - "+str(nThreadsCount)
writeLine=writeLine+","+str(nThreadsCount)

if (CriticalPath<=14):
  print "Critical Path - L"
  writeLine=writeLine+",L"
else :
  print "Critical Path - H"
  writeLine=writeLine+",H"
writeLine=writeLine+"\n"
with open('Output.txt','ab') as apfile:
  apfile.write(writeLine);
