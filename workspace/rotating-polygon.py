from Tkinter import * 
import math 

c = Canvas(width=200, height=200) 
c.pack()

# a square
xy = [(50, 50), (150, 50), (150, 150), (50, 150)] 
# line
#xy = [(50, 50), (150, 150), (150, 155), (50, 55)]  # added
polygon_item = c.create_polygon(xy) 
center = 100, 100
#c.coords(polygon_item, 50, 50, 150, 150, 150, 155, 50, 55)

def getangle(event):
    #dx = c.canvasx(event.x) - center[0]
    #dy = c.canvasy(event.y) - center[1]
    #print str(c.canvasx(event.x)) + " " + str(center[0]) + ", " + str(c.canvasy(event.y)) + " " + str(center[1]) # added
    #print str(dx) + " " + str(dy)  # added
    dx = event.x - origin[0]  # added
    dy = event.y - origin[1]  # added
    #print str(event.x) + " " + str(origin[0]) + ", " + str(event.y) + " " + str(origin[1]) # added
    try:
        #print complex(dx, dy) / abs(complex(dx, dy))
        return complex(dx, dy) / abs(complex(dx, dy))
    except ZeroDivisionError:
        return 0.0 # cannot determine angle 

def press(event):
    global origin  # added
    origin = event.x, event.y + 10   # added
    #print str(origin[0]) + " " + str(origin[1])  # added

    # calculate angle at start point
    global start
    start = getangle(event)

def motion(event):
    # calculate current angle relative to initial angle
    global start
    angle = getangle(event) / start
    offset = complex(center[0], center[1])
    #print str(origin[0]) + " " + str(origin[1])  # added
    newxy = []
    for x, y in xy:
        v = angle * (complex(x, y) - offset) + offset
        newxy.append(v.real)
        newxy.append(v.imag)
    c.coords(polygon_item, *newxy) 

c.bind("<Button-1>", press) 
c.bind("<B1-Motion>", motion) 

mainloop()
