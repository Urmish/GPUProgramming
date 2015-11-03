import re

print "Hi"

def generateAST(currentLine): 
  currentLineStripped = currentLine.strip()
  print "generateAST for "+currentLineStripped
  possibleComment = re.match('^//',currentLineStripped)
  if(possibleComment):
    print "This line is a comment"
    return 0
  trailComments = re.findall('//.*',currentLineStripped)
  if (trailComments):
    currentLineStripped = currentLineStripped.replace(trailComments[0],"")
  checkFor = re.findall(r'\bfor\b',currentLineStripped)
  if (checkFor):
    print "This line is a for"
    return 1
  iterMatch = re.finditer("\w+\[[^\[].*?\]\[[^\[].*?\]",currentLineStripped) #2D Array
  tempLine = currentLineStripped
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    #print s
    #print e
    s = s-remLength
    e = e-remLength 
    #print tempLine[0:s]
    #print tempLine[e:]
    if s>0:
      tempLine = tempLine[0:s] + "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    elif s==0:
      tempLine = "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    #print tempLine
    #print remLength
  print tempLine
  iterMatch = re.finditer("\w+\[[^\]]*?\[.*?[^\]]\[.*?\][^\[]*?\]\]",tempLine)
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    #print s
    #print e
    s = s-remLength
    e = e-remLength 
    if s>0:
      tempLine = tempLine[0:s] + "#3#" + tempLine[e:]
      remLength= remLength + e-s - 3 
    elif s==0:
      tempLine = "#3#" + tempLine[e:]
      remLength= remLength + e-s - 3

  print tempLine
  iterMatch = re.finditer("\w+\[[^\]]*?\[.*?\][^\[]*?\]",tempLine)
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    #print s
    #print e
    s = s-remLength
    e = e-remLength 
    if s>0:
      tempLine = tempLine[0:s] + "#2#" + tempLine[e:]
      remLength= remLength + e-s - 3 
    elif s==0:
      tempLine = "#2#" + tempLine[e:]
      remLength= remLength + e-s - 3

  print tempLine
  iterMatch = re.finditer("\w+\[[^\[].*?\]",tempLine) 
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    #print s
    #print e
    s = s-remLength
    e = e-remLength 
    #print tempLine[0:s]
    #print tempLine[e:]
    if s>0:
      tempLine = tempLine[0:s] + "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    elif s==0:
      tempLine = "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    #print tempLine
    #print remLength
  print tempLine

  iterMatch = re.finditer("#(\d)#\.#(\d)#",tempLine)
  remLength = 0
  for match in iterMatch:
    d1 = match.group(1)
    d2 = match.group(2)
    d3 = int(d2)
    if (int(d1)>int(d2)):
      d3 = int(d1)
    [s, e] = match.span()
    s = s-remLength
    e = e-remLength 
    #print s 
    #print e
    if s>0:
      tempLine = tempLine[0:s] + "#"+ str(d3+1)+"#" + tempLine[e:]
      remLength= remLength + e-s - 3
    elif s==0:
      tempLine = "#"+ str(d3+1)+"#" + tempLine[e:]
      remLength= remLength + e-s - 3
  print tempLine

  iterMatch = re.finditer("\w+\.#(\d)#",tempLine)
  remLength = 0
  for match in iterMatch:
    d1 = match.group(1)
    d3 = int(d1)
    [s, e] = match.span()
    s = s-remLength
    e = e-remLength 
    #print s 
    #print e
    if s>0:
      tempLine = tempLine[0:s] + "#"+ str(d3+1)+"#" + tempLine[e:]
      remLength= remLength + e-s - 3
    elif s==0:
      tempLine = "#"+ str(d3+1)+"#" + tempLine[e:]
      remLength= remLength + e-s - 3
  print tempLine
 
  tempLine = re.sub(r'if',"0=",tempLine) #if statements
  tempLine = re.sub(r'}',"",tempLine)
  tempLine = re.sub(r'{',"",tempLine)
  tempLine = re.sub(r'float ',"",tempLine)
  tempLine = re.sub(r'int ',"",tempLine)
  tempLine = re.sub(r'double ',"",tempLine)
  #Every memory operation should be replaced by now, Now we need to change the other variable names to #0# as they could be loaded instantly
  #3 types of variables
  #1. mix letters and digits, temp3
  #2. only words
  #3. only digits (constants) NEED TO AVOID #2# patterns, probably "[^#]\d+[^#]" - DOESNT WORK
  tempLine = re.sub(r"[0-9]+\.[0-9]+f","#0#",tempLine) #Replcae floating point decimal
  tempLine = re.sub(r"[a-zA-Z]+[0-9]+[a-zA-Z]+","#0#",tempLine)
  tempLine = re.sub(r"[a-zA-Z]+_+[a-zA-Z]+","#0#",tempLine) #Test1 has new_dw
  tempLine = re.sub(r"[a-zA-Z]+[0-9]+","#0#",tempLine)
  tempLine = re.sub(r"[a-zA-Z]+","#0#",tempLine)
  #tempLine = re.sub(r"[^#][0-9]+[^#]","#0#",tempLine) #This is wrong as even +1 is replaced with #0# since +1 obeys the pattern of no [^#] expr
  #Need to replace all digits with space digit space format
  print tempLine
  tempLine = re.sub(r'([^a-zA-Z0-9#\.]+?)', r' \1 ',tempLine) #. represents a decimal point
  print tempLine
  tempLine = re.sub(r' \d+\.\d+ ',"#0#",tempLine) #Replace Decimal Values first, of the form 0.9
  tempLine = re.sub(r' \.\d+ ',"#0#",tempLine) #Replace Decimal Values first of the form .9
  print tempLine
  tempLine = re.sub(r' [0-9]+ ',"#0#",tempLine)
  print tempLine
  tempLine = re.sub(r'\s+',"",tempLine)
  print tempLine
  #Need to replace all digits with space digit space format
  tempLine = re.sub(r'#',"",tempLine)
  tempLine = re.sub(r';',"",tempLine)
  tempLine = re.sub(r'(.*)\+=',r'\1=\1\+',tempLine)
  tempLine = re.sub(r'=-(\d)',r'=\1',tempLine)
  print tempLine
  keepGoing = True
  foundRHS = False
  defaultOperandValue = -99
  startIdxPos = 1
  tempLine2 = tempLine.strip()
  checkEqual = re.search(r'[^<>=]=',currentLineStripped)
  if (bool(checkEqual) == False):
    print "This line does not have an ="
    return 0
  while keepGoing == True:
    #print "In While\n"
    startIdx = startIdxPos
    operand1=defaultOperandValue
    operand2=defaultOperandValue
    start = 9999
    end   = 9999
    while (startIdx < len(tempLine2)):
      if foundRHS == False:
        if (tempLine2[startIdx] == "=" and (tempLine2[startIdx-1] != "=" and tempLine2[startIdx-1] != "<" and tempLine2[startIdx-1] != ">")):
          foundRHS = True
          startIdxPos = startIdx+1
        else:
          foundRHS=False
      else:
	currentChar = tempLine2[startIdx]
  	if (currentChar=="(" or currentChar==")"):
  	  operand1 = defaultOperandValue
  	  operand2 = defaultOperandValue
  	elif(bool(re.search("\d",currentChar))):
  	  if(operand1 !=defaultOperandValue):
  	    operand2 = int(currentChar)
  	    end = startIdx
  	    #print tempLine2
  	    tempLine2 = tempLine2[0:start] + str(max(operand1,operand2)+1) + tempLine2[end+1:]
  	    #print tempLine2
  	    startIdx = start + len(str(max(operand1,operand2)+1))
  	    start = 9999
  	    end = 9999
  	    operand1=defaultOperandValue
  	    operand2=defaultOperandValue
  	  else:
  	    operand1 = int(currentChar)
  	    start = startIdx
      startIdx=startIdx+1
      #print "Start Index is " + str(startIdx)
      #print "Length is " + str(len(tempLine2))
      #print tempLine2
      tempLine2 = re.sub(r'\((\d)\)',r'\1',tempLine2)
      #print tempLine2+"\n"
      if(bool(re.search(r'\d.*=\d$',tempLine2))):
	keepGoing=False
	break
      #keepGoing=False
    
  match = re.search(r'(\d).*=(\d)$',tempLine2)
  print "Time Taken "+str(max(int(match.group(1)),int(match.group(2))))+"\n"
  return str(max(int(match.group(1)),int(match.group(2))))

#Test Vectors
#testVec1 = "if((accessKnode.keys[thid] <= start[bid]) && (accessKnode.keys[thid+1] > start[bid])){"
#testVec2 = "offset_2[bid] = knodes[access3].indices[thid];"
#testVec3 = "reclength[bid] = knodes[access4].indices[thid] - recstart[bid]+1;"
#testVec4 = "dN[k] = image[i-1 + Nr*j] - Jc;"
#testVec5 = "G2 = (temp1*temp1 + temp2*temp2 + temp3*temp3 + temp4*temp4) / (Jc*Jc);"
#testVec6 = "u1_r[idx] = u0_r[idx] * ex[t*indexmap[idx]];"
#testVec7 = "offset_2[bid] = knodes[access3].indices[thid] + efc + adasd + 4 + knodes[access3].indices[thid];"
#testVec8 = "A = A[i][k]"
#generateAST(testVec1)
#generateAST(testVec2)
#generateAST(testVec3)
#generateAST(testVec4)
#generateAST(testVec5)
#generateAST(testVec6)
#generateAST(testVec7)
