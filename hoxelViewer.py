import hoxlib
from graphics import *
files=[]
for filename in os.listdir("hox"):
    if filename.endswith(".json") or filename.endswith(".hox") or filename.endswith(".qoh") or filename.endswith(".qob"):
        files.append(filename)
    else:
        continue

windowWidth=750
windowHeight=750
bl=4
size=3

sm=1
lg=6
tileSize=(windowWidth-lg*6-sm*20)/25
win=GraphWin("4D Miner Editor",windowWidth,windowHeight,autoflush=False)
win.setBackground("white")
selectedFile=0

elements=[]
def drawFileNames():
    for i in range(10):
        fileNo=selectedFile+5-i
        if (fileNo>-1 and fileNo<len(files)):
            if fileNo==selectedFile:
                rect=Rectangle(Point(0,3*lg+20*(i)),Point(windowWidth,3*lg+20*(i+1)))
                rect.setFill(color_rgb(0,255,0))
                rect.draw(win)
                elements.append(rect)
            text=Text(Point(lg+70,lg+20*(i+1)),files[fileNo])
            text.draw(win)
            elements.append(text)

   

drawFileNames()
key=""

while not key=="Return":
    key=win.getKey()
    if key=="w":
        if selectedFile<len(files)-1:
            selectedFile=selectedFile+1
            for e in elements:
                e.undraw()
            elements=[]
            drawFileNames()
    elif key=="s":
        if selectedFile>0:
            selectedFile=selectedFile-1
            for e in elements:
                e.undraw()
            elements=[]
            drawFileNames()
for e in elements:
    e.undraw()
elements=[]

model=hoxlib.loadHoxelModel("hox/"+files[selectedFile])

class camera:
    def __init__(self,pos):
        self.pos=pos
        self.elements=[]

    def contains(self,p):
        return p[0] >= self.pos[0] and p[0] <= self.pos[0] + 4 and p[1] >= self.pos[1] and p[1] <= self.pos[1] + 4 and p[2] >= self.pos[2] and p[2] <= self.pos[2] + 4 and p[3] >= self.pos[3] and p[3] <= self.pos[3] + 4
    
    def getScreenPos(self,p):
        trans=[p[i] - self.pos[i] for i in range(4)]
        
        return Point(
            round(trans[0]*(tileSize+sm)+trans[3]*(tileSize*5+sm*4+lg)+lg),
            round((4-trans[1])*(tileSize+sm)+(4-trans[2])*(tileSize*5+sm*4+lg))+lg
        )
    
    def move(self,v):
        self.pos=[self.pos[i] + v[i] for i in range(4)]

    def draw(self,window):
        
        newElements=[]
        exceptions=[]
        for i in range(5):
            for k in range(5):
                for j in range(5):
                    for l in range(5):
                        wp=[self.pos[0]+i,self.pos[1]+j,self.pos[2]+k,self.pos[3]+l]
                        if (wp[0] > -1 and wp[0] < model["width"]) and (wp[1] > -1 and wp[1] < model["height"]) and (wp[2] > -1 and wp[2] < model["length"]) and (wp[3] > -1 and wp[3] < model["trength"]):
                            sp=self.getScreenPos(wp)
                            sp2=Point(sp.getX()+tileSize,sp.getY()+tileSize)
                            hox=Rectangle(sp,sp2)
                            c=model["col"][hoxlib.flattenCA(wp,model["width"],model["height"],model["length"],model["trength"])]
                            hox.setFill(color_rgb(c[0],c[1],c[2]))
                            if hox in self.elements:
                                exceptions.append(hox)
                            else:
                                hox.draw(window)
                            newElements.append(hox)
        crect=Rectangle(Point(lg+2,lg+2),Point(lg+140,lg+30))
        crect.setFill(color_rgb(255,255,255))
        crect.draw(window)
        newElements.append(crect)
        coords=Text(Point(lg+70,lg+20),"X: "+str(self.pos[0]+2)+" Y:"+str(self.pos[1]+2)+" Z:"+str(self.pos[2]+2)+" W:"+str(self.pos[3]+2))
        coords.draw(window)
        newElements.append(coords)

        self.partialUndraw(exceptions)
        self.elements=newElements

    def undraw(self):
        for e in self.elements:
            e.undraw()
        self.elements=[]
    
    def partialUndraw(self,exceptions):
        for e in self.elements:
            if not e in exceptions:
                e.undraw()
        self.elements=exceptions


cam=camera([2,2,2,2])
cam.draw(win)

key=""

while not key=="Escape":
    key=win.getKey()
    if key=="w":
        cam.move([0,0,1,0])
        cam.draw(win)
    elif key=="s":
        cam.move([0,0,-1,0])
        cam.draw(win)
    elif key=="d":
        cam.move([1,0,0,0])
        cam.draw(win)
    elif key=="a":
        cam.move([-1,0,0,0])
        cam.draw(win)
    elif key=="e":
        cam.move([0,0,0,1])
        cam.draw(win)
    elif key=="q":
        cam.move([0,0,0,-1])
        cam.draw(win)
    elif key=="space":
        cam.move([0,1,0,0])
        cam.draw(win)
    elif key=="Shift_L":
        cam.move([0,-1,0,0])
        cam.draw(win)