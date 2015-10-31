import re

print "Hi"

def generateAST(currentLine): 
  iterMatch = re.finditer("\w+\[[^\[].*?\]\[[^\[].*?\]",currentLine) #2D Array
  tempLine = currentLine
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    print s
    print e
    s = s-remLength
    e = e-remLength 
    print tempLine[0:s]
    print tempLine[e:]
    if s>0:
      tempLine = tempLine[0:s] + "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    print tempLine
    print remLength
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
  print tempLine
  iterMatch = re.finditer("\w+\[[^\[].*?\]",tempLine) 
  remLength = 0
  for i in iterMatch:
    [s,e] = i.span()
    print s
    print e
    s = s-remLength
    e = e-remLength 
    print tempLine[0:s]
    print tempLine[e:]
    if s>0:
      tempLine = tempLine[0:s] + "#1#" + tempLine[e:]
      remLength= remLength + e-s - 3
    print tempLine
    print remLength
  print tempLine
  return

#Test Vectors
#cl1 = "if((accessKnode.keys[thid] <= start[bid]) && (accessKnode.keys[thid+1] > start[bid])){"
#cl2 = "offset_2[bid] = knodes[access3].indices[thid];"
#cl3 = "reclength[bid] = knodes[access4].indices[thid] - recstart[bid]+1;"
#cl4 = "dN[k] = image[i-1 + Nr*j] - Jc;"
#cl5 = "G2 = (temp1*temp1 + temp2*temp2 + temp3*temp3 + temp4*temp4) / (Jc*Jc);"
#cl6 = "cl6 = "u1_r[idx] = u0_r[idx] * ex[t*indexmap[idx]];"
#Done!

