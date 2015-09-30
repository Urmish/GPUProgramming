import re
startFrom = 0
currentLine = "B[i]= A[i+4]*B[i+8] + C*D+ (E * F)"
print currentLine
matches = re.finditer("\*",currentLine)
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
    if (currentLine[start] == "]"):
      operandA = 2
      while (currentLine[start] != "["):
	start=start-1  
      start=start-1 #Just Reached [, need to decrement
    print currentLine[startFrom:start+1]
    temp = re.search('[ *=/\(\+](\w.*)$',currentLine[startFrom:start+1])
    if temp:
      print "match"
      print temp.group(1)
    else:
      operandA=3 #If no variable found, then its a constant
    startFrom = end 
    print currentLine[startFrom:]
    temp = re.search('(\w.*?)[ +*/\[\)]',currentLine[startFrom:])
    if temp:
      print "match"
      print temp.group(1)
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
