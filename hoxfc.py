import json
import os
import traceback
import time
import copy
directory = "hox"
TO_HOX = 0
TO_QOH = 1

EOF=bytes([0]*7+[1])
#print(EOF)

headerSize=22
channels=4
eofSize=8
tagMask=int("11000000",2)
lastTwoBitsMask=int("00000011",2)
lastFourBitsMask=int("00001111",2)
lastSixBitsMask=int("00111111",2)
RGB=int("11111110",2)
RGBA=int("11111111",2)
INDEX=int("00000000",2)
DIF=int("01000000",2)
LUMA=int("10000000",2)
RUN=int("11000000",2)

files=[]
for filename in os.listdir(directory):
    if filename.endswith(".json") or filename.endswith(".hox") or filename.endswith(".qoh") or filename.endswith(".qob"):
        files.append(filename)
    else:
        continue

data={}
hox=[]
col=[]
mat=[]
bins=bytearray("qohf","utf-8")
prehox=[0,0,0,255]

width=0
height=0
length=0
trength=0

def flatten(x,y,z,w,width,height,length,trength):
    return x+y*width+z*width*height+w*width*height*length

def unflatten(i,width,height,length,trength):
    return {"x":i%width, "y":(i//width)%height, "z":(i//(width*height))%length, "w":(i//(width*height*length))%trength}

def writeInt(i,barray):
    bi=i.to_bytes(4,"big")
    barray.append(bi[0])
    barray.append(bi[1])
    barray.append(bi[2])
    barray.append(bi[3])

def hash(color):
    return (color[0]*3+color[1]*5+color[2]*7+color[3]*11)%64

def getMaxFileSize(width,height,length,trength,channels=4):
    return headerSize+width*height*length*trength*(channels+1)+eofSize

def compColor(c1,c2):
    return (c1[0]==c2[0] and c1[1]==c2[1] and c1[2]==c2[2] and c1[3]==c2[3])

"""
#flattening and unflattening testing

test=[None]*8*8*8*8
for w in range(8):
    for z in range(8):
        for y in range(8):
            for x in range(8):
                print("("+str(x)+","+str(y)+","+str(z)+","+str(w)+")  ==>  "+str(flatten(x,y,z,w,8,8,8,8)))
                test[flatten(x,y,z,w,8,8,8,8)]={"x":x, "y":y, "z":z, "w":w}

for i in range(8*8*8*8):
    p=unflatten(i,8,8,8,8)
    x=p["x"]
    y=p["y"]
    z=p["z"]
    w=p["w"]
    print(str(i) + " ==>  "+"("+str(x)+","+str(y)+","+str(z)+","+str(w)+")")

    #This makes sure that the functions are inverses
    if (test[i]==p):
        print("Yay!")
    else:
        print("Error! bad test!")
        input()
"""
try:
    i=0
    for filename in files:
        print("["+str(i)+"] : "+filename)
        i=i+1
    i=int(input("File ID: "))
    
    filename=files[i]
    filenameNoExt=filename
    if (filename.endswith(".json")):
        conversionType=TO_QOH
        filenameNoExt=filename[:len(filename)-5]
    elif (filename.endswith(".hox")):
        conversionType=TO_QOH
        filenameNoExt=filename[:len(filename)-4]
    elif (filename.endswith(".qoh")):
        conversionType=TO_HOX
        filenameNoExt=filename[:len(filename)-4]
    elif (filename.endswith(".qob")):
        conversionType=TO_HOX
        filenameNoExt=filename[:len(filename)-4]
    
    print("You have selected [ "+filenameNoExt+" ] to be converted.")

    if (conversionType==TO_HOX):
        with open("hox/"+filenameNoExt+".hox", "w") as out:
            with open("hox/"+filename, "rb") as f:
                print("Loading "+filename+"...")
                print("Converting data...")
                bins=f.read()
                #decode binary qoh data

                #get data from header
                width=int.from_bytes(bins[4:8],"big")
                height=int.from_bytes(bins[8:12],"big")
                length=int.from_bytes(bins[12:16],"big")
                trength=int.from_bytes(bins[16:20],"big")
                bulk=width*height*length*trength
                channels=bins[20]
                print("Model size: "+str(width)+" x "+str(height)+ " x "+str(length)+" x "+str(trength))
                print("Model bulk: "+str(bulk))
                print("Channels: "+str(channels))
                print("Color space: "+("sRGB with linear alpha" if bins[21]==0 else "all channels linear"))#the color space is just informative so we don't need to store it
                #iterate through remaining bytes (go until you see the eof code or there are not enough bytes for the eof code to encoded with in the unread bytes)
                col=[[0,0,0,0]]*bulk
                i=22
                c=0
                recentColorArray=[[0,0,0,0]]*64
                prehox=[0,0,0,255]
                while bins[i:i+eofSize]!=EOF and i<len(bins):
                    #check for 8-bit tags first
                    if (bins[i]==RGB):
                        #print("RGB")
                        #decode rgb
                        col[c]=[int.from_bytes(bins[i+1:i+2],"big"),int.from_bytes(bins[i+2:i+3],"big"),int.from_bytes(bins[i+3:i+4],"big"),prehox[3]]
                        recentColorArray[hash(col[c])]=col[c]
                        #we decoded 3 more bytes so increase i by 3
                        prehox=col[c]
                        #print(col[c])
                        i=i+3
                        c=c+1
                        
                    elif (bins[i]==RGBA):
                        #decode rgba
                        #print("RGBA")
                        col[c]=[int.from_bytes(bins[i+1:i+2],"big"),int.from_bytes(bins[i+2:i+3],"big"),int.from_bytes(bins[i+3:i+4],"big"),int.from_bytes(bins[i+4:i+5],"big")]
                        recentColorArray[hash(col[c])]=copy.deepcopy(col[c])
                        #print(col[c])
                        #we decoded 4 more bytes so increase i by 3
                        prehox=col[c]
                        
                        #print(col[c])
                        i=i+4
                        c=c+1
                    elif (bins[i] & tagMask==INDEX):
                        #decode index
                        #print("INDEX")
                        #use color from recent color array at hash index (we don't need to store it in there this time since we know it's already there)
                        col[c]=recentColorArray[bins[i] & int("00111111",2)]
                        prehox=col[c]
                        #print(col[c])
                        c=c+1
                    elif (bins[i] & tagMask==DIF):
                        #decode dif
                        #print("DIF")
                        dr=((bins[i]>>4) & lastTwoBitsMask)-2
                        dg=((bins[i]>>2) & lastTwoBitsMask)-2
                        db=(bins[i] & lastTwoBitsMask)-2
                        col[c]=[(prehox[0]+dr)%256,(prehox[1]+dg)%256,(prehox[2]+db)%256,prehox[3]]
                        recentColorArray[hash(col[c])]=col[c]
                        prehox=col[c]
                        #print(col[c])
                        c=c+1
                    elif (bins[i] & tagMask==LUMA):
                        #decode luma
                        #print("LUMA")
                        
                        dg=(bins[i] & lastSixBitsMask)-32

                        #the second byte is split into two four bit numbers that are dr-dg and db-dg and have a bias of 8 so we get those numbers, subtract 8 for the bias,and add the dg to each to get the dr and the db
                        dr=((bins[i+1]>>4) & lastFourBitsMask)-8+dg
                        db=((bins[i+1]) & lastFourBitsMask)-8+dg
                        col[c]=[(prehox[0]+dr)%256,(prehox[1]+dg)%256,(prehox[2]+db)%256,prehox[3]]
                        prehox=copy.deepcopy(col[c])
                        #print(col[c])
                        recentColorArray[hash(col[c])]=col[c]
                        c=c+1
                        #we decoded 1 more byte so increase i by 1
                        i=i+1
                    elif (bins[i] & tagMask==RUN):
                        #print("RUN")
                        #decode run
                        for j in range((bins[i] & lastSixBitsMask)+1): #we add one because the run length is encoded with a bias of -1 
                            col[c]=copy.deepcopy(prehox)
                            c=c+1
                        #print(str(col[c-1])+" x "+str(j+1))
                    #print("prehox: "+str(prehox))
                    #We always decode at least one bit
                    i=i+1
            #input()
            #TODO set data to what I want the data to be before writing to the file
            #Generate mats and fill hoxel array at the same time
            c=0
            newMatIndex=1
            mat=[{"albedo":{"b":0.0,"g":0.0,"r":0.0}}]*255
            for item in col:
                #only do stuff with visible colors
                #print(item)
                if (item[3]>0):
                    #put the color into materials if it isn't there already (there can't be more than 255 materials not counting the invisible material)
                    if (not ({"albedo":{"b":item[2]/255,"g":item[1]/255,"r":item[0]/255}} in mat) and newMatIndex<255):
                        mat[newMatIndex]={"albedo":{"b":item[2]/255,"g":item[1]/255,"r":item[0]/255}}
                        newMatIndex=newMatIndex+1
                    m=0
                    for matItem in mat:
                        if (matItem=={"albedo":{"b":item[2]/255,"g":item[1]/255,"r":item[0]/255}}):
                            break
                        m=m+1
                    if(m>254):
                        m=254
                    coords=unflatten(c,width,height,length,trength)
                    hox.append({"i":[coords["x"],coords["y"],coords["z"],coords["w"]],"m":m})
                c=c+1    
            data={"materials":mat
                ,"scene":{
                    "hoxelGrids":[{
                        "data":hox,
                        "dimensions":{
                            "x":width,
                            "y":height,
                            "z":length,
                            "w":trength
                        },
                        "rotXW":0.0,
                        "rotXY":0.0,
                        "rotYW":0.0,
                        "rotZW":0.0,
                        "translation":{"w":0.0,"x":0.0,"y":0.0,"z":0.0}
                    }]
                }
            }
            

            print("Writing output file...")
            json.dump(data,out)
            print("File conversion complete!")
    else:
        with open("hox/"+filenameNoExt+".qoh", "wb") as out:
            with open("hox/"+filename, "r") as f:
                print("Loading "+filename+"...")
                newData=json.load(f)
                #print(newData)
                for item in newData:
                    data[item]=(newData[item])
                
                #Organize data into useful variables

                #print(data)
                for item in data["materials"]:
                    mcolor=item["albedo"]
                    mat.append([mcolor["r"],mcolor["g"],mcolor["b"],255])
                #print(mat)

                dims=data["scene"]["hoxelGrids"][0]["dimensions"]
                #print(dims)
                width=dims["x"]
                height=dims["y"]
                length=dims["z"]
                trength=dims["w"]
                bulk=width*height*length*trength
                fsize=getMaxFileSize(width,height,length,trength)
                if fsize>1000:
                    print("Max file size of file after conversion to qoh: "+str(fsize/1000)+" KB")
                else:
                    print("Max file size of file after conversion to qoh: "+str(fsize)+" bytes")
                col=[[0, 0, 0, 0]]*bulk
                for item in data["scene"]["hoxelGrids"][0]["data"]:
                    color=mat[item["m"]]
                    col[flatten(item["i"][0],item["i"][1],item["i"][2],item["i"][3],width,height,length,trength)]=[int(color[0]*255),int(color[1]*255), int(color[2]*255), color[3]] #non-alpha channels are stored in a range from 0.0 to 1.0 so we need to convert those to integers between 0 and 255
                #print(col)

                prehox=[0,0,0,255]
                runCount=0
                recentColorArray=[[0,0,0,0]]*64

                #Encode binary qoh data

                #continue writing header (bins was initialised with 'qohf' written already)
                writeInt(width,bins)
                writeInt(height,bins)
                writeInt(length,bins)
                writeInt(trength,bins)
                bins.append(4) #channels = 4 (RGBA)
                bins.append(1) #color space = 1 (all channels linear)

                #end of header

                for i in range(bulk):
                    color=col[i]
                    #input()
                    #print(color)
                    #print(prehox)
                    #print(runCount)
                    #if the color of the hoxel that we're on is the same as the last one then we have a run
                    if (compColor(prehox,color)):
                        runCount=runCount+1
                        #print("On a RUN")
                        #if there was a run of 62 (the longest run we can encode in a run chunk) or if we are on the last hoxel then write the run chunk
                        if (runCount==62 or i==bulk-1):
                            #print("Write RUN")
                            bins.append(int('11000000',2) + runCount-1)
                            runCount=0
                    else:
                        if (runCount>0):
                            bins.append(int('11000000',2) + runCount-1)
                            #print("Write RUN")
                        #there wasn't actually a run or the run ended so try something else for the current hoxel
                        #try INDEX OP
                        hashIndex=hash(color)

                        #print(color)
                        #print(recentColorArray[hashIndex])
                        if (compColor(color,recentColorArray[hashIndex])):
                            #print("Write INDEX")
                            bins.append(hashIndex)
                        else:
                            recentColorArray[hashIndex]=copy.deepcopy(color)
                            if (color[3]==prehox[3]):
                                #try DIF OP
                                dcolor=[(color[0]-prehox[0]),(color[1]-prehox[1]),(color[2]-prehox[2]),color[3]]
                                if (dcolor[0]>-3 and dcolor[0]<2 and dcolor[1]>-3 and dcolor[1]<2 and dcolor[2]>-3 and dcolor[2]<2):
                                    #print("Write DIF")
                                    bins.append(int('01000000',2)+(dcolor[0]+2)*2**4+(dcolor[1]+2)*2**2+(dcolor[2]+2))
                                else:
                                    #try LUMA OP
                                    
                                    drdg=dcolor[0]-dcolor[1]
                                    dbdg=dcolor[2]-dcolor[1]
                                    if (drdg>-9 and drdg<8 and dcolor[1]>-33 and dcolor[1]<32 and dbdg>-9 and dbdg<8):
                                        #print("Write LUMA")
                                        bins.append(int('10000000',2)+(dcolor[1]+32))
                                        bins.append((drdg+8)*2**4+(dbdg+8))

                                    else:
                                        #print("Write RGB")
                                        #try RGB OP
                                        bins.append(int('11111110',2))
                                        bins.append(color[0])
                                        bins.append(color[1])
                                        bins.append(color[2])
                            else:
                                #if all else fails, write all the color data with an RGBA OP
                                #print("Write RGBA")
                                bins.append(int('11111111',2))
                                bins.append(color[0])
                                bins.append(color[1])
                                bins.append(color[2])
                                bins.append(color[3])
                        #reset run count because the run has been broken
                        runCount=0
                    prehox=color
                
            print(bins)
            print("Writing output file...")
            out.write(bytes(bins))
            print("File conversion complete!")

                


except:
    traceback.print_exc()
    print("Error! Please note that for some reason extra commas are not tolerated, so that may be the issue.")

os.system("pause")