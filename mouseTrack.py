# All packages needed for the program are imported ahead
import cv2
import numpy as np
import pyautogui
import time

pyautogui.FAILSAFE
#Global variables accessible to all modules
prevSc = 0

# colour ranges for feeding to the inRange funtions
blueRange = np.array([[88,78,20],[128,255,255]])
greenRange = np.array([[45,100,50],[75,255,255]])
redRange = np.array([[190,0,0],[255,255,255]])

# Rectangular kernal for eroding and dilating the mask for primary noise removal 
kernel = np.ones((7,7),np.uint8) 

# Prior initialization of all centers for safety
t_cen, i_cen, m_cen = [240,320],[240,320],[240,320]

Simulate = False

#when flag is true then goes to calibration window
flag = True

#function which returns nothing
def nothing():
    pass

# Distance between two centroids
def distance( c1, c2):
    distance = pow( pow(c1[0]-c2[0],2) + pow(c1[1]-c2[1],2) , 0.5)
    return distance

#Draw Contour 
def trackFinger(finger, colorRange, image):
    
    if (finger == 'T'):
        mask = cv2.inRange(image, colorRange[0], colorRange[1])
        eroded = cv2.erode( mask, kernel, iterations=1)
        dilated = cv2.dilate( eroded, kernel, iterations=1)
    elif (finger == 'I'):
        mask = cv2.inRange(HSVImage, colorRange[0], colorRange[1])
        eroded = cv2.erode( mask, kernel, iterations=1)
        dilated = cv2.dilate( eroded, kernel, iterations=1)
    elif (finger == 'M'):
        mask = cv2.inRange(HSVImage, colorRange[0], colorRange[1])
        eroded = cv2.erode( mask, kernel, iterations=1)
        dilated = cv2.dilate( eroded, kernel, iterations=1)
    
    #Get contour and length of contours
    contour, _ = cv2.findContours( dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    l=len(contour)
    #Area for every contour stored here
    area = np.zeros(l)
    #check for appropriate areas only
    for i in range(l):
        if cv2.contourArea(contour[i])>100 and cv2.contourArea(contour[i])<1700:
            area[i] = cv2.contourArea(contour[i])
        else:
            area[i] = 0
            
    #sort area in decending order
    a = sorted( area, reverse=True)	
    
    #sort contour in terms of area in decending order
    # bringing contours with largest valid area to the top
    for i in range(l):
        for j in range(1):
            if area[i] == a[j]:
                temp = contour[i]
                contour[i] = contour[j]
                contour[j] = temp
                
    if l > 0 :		
		# finding centroid using method of 'moments'
        ''' Here M['m00'] is area 
            and  M['m01'] is sum of x-cordinates
            centroidX = sum of x-coordinates/Area
            and same for y
        '''
        M = cv2.moments(contour[0])
        if M['m00'] != 0:
            #Points can not be floating so int() used
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            center = (cx,cy)		
            return center
        else:
            return (-1,-1)
    else:
        return (-1,-1)
#Calibration module returns colorRange
def calibrateFinger(finger, colorRange):
    global kernel
    # giving name of window according to the finger calibration
    if (finger == 'T'):
        name = 'Calibrate Thumb'
    elif (finger == 'I'):
        name = 'Calibrate Index'
    elif (finger == 'M'):
        name = 'Calibrate Middle'
        
    #create a new window with respecctive names    
    cv2.namedWindow(name)
    
    #creates trackbar in the repective window
    cv2.createTrackbar('Hue', name, colorRange[0][0]+20, 180, nothing)
    cv2.createTrackbar('Sat', name, colorRange[0][1]   , 255, nothing)
    cv2.createTrackbar('Val', name, colorRange[0][2]   , 255, nothing)
    
    # to read image from video make an infinite loop
    while (1):
        
        # Get a hsv image from capture
        ret, frame = cap.read()
        flipped=cv2.flip(frame ,1)
        HSVImage = cv2.cvtColor(flipped, cv2.COLOR_BGR2HSV)
        
        #get HSV value from TrackBar
        hue = cv2.getTrackbarPos('Hue', name)
        sat = cv2.getTrackbarPos('Sat', name)
        val = cv2.getTrackbarPos('Val', name)
        
        
        lower = np.array([hue-20,sat,val])
        upper = np.array([hue+20,255,255])

        #Morphosism noise cancellation
        mask = cv2.inRange(HSVImage, lower, upper)
        eroded = cv2.erode( mask, kernel, iterations=1)
        dilated = cv2.dilate( eroded, kernel, iterations=1)
         
        
        cv2.imshow(name, dilated)
        k = cv2.waitKey(1)
        if k == 32:
            break
    cv2.destroyWindow(name)
    return np.array([[hue-20,sat,val],[hue+20,255,255]])


'''
This function takes as input the center of blue region ( thump center) and 
the previous cursor position (pyp). The new cursor position is calculated 
in such a way that the mean deviation for desired steady state is reduced.
'''
def setCursorPos( tc, ptp):
	
	tp = np.zeros(2)
	
	if abs(tc[0]-ptp[0])<5 and abs(tc[1]-ptp[1])<5:
		tp[0] = tc[0] + .7*(ptp[0]-tc[0]) 
		tp[1] = tc[1] + .7*(ptp[1]-tc[1])
	else:
		tp[0] = tc[0] + .1*(ptp[0]-tc[0])
		tp[1] = tc[1] + .1*(ptp[1]-tc[1])
	
	return tp	


def chooseOption(tc, ic, mc): 
    global prevSc
    if ic[0]!=-1 and mc[0]!=-1:
        if (distance(tc,ic) < 38) and (distance(tc,mc) > 38):
            prevSc = 0
            return 'left'
        elif (distance(tc,mc) < 37) and (distance(tc,ic) > 37):
            prevSc = 0
            return 'right'
        elif (distance(ic,mc) < 40) and (distance(tc,ic) > 100) and (distance(tc, mc) > 40):
            return 'scroll'
        elif (distance(tc,ic) < 50) and (distance(tc,mc) < 50) and (distance(ic, mc) < 50):
            prevSc = 0
            return 'drag'
        else:
            prevSc = 0
            return 'move'
    else:
        return -1
        
def performAction(action, tc, ic, mc):
    global prevSc
    if action == 'move':
        #Move cursor through out screen
        if tc[0]>110 and tc[0]<590 and tc[1]>120 and tc[1]<390:
            pyautogui.moveTo(4*(tc[0]-110),4*(tc[1]-120))
        elif tc[0]<110 and tc[1]>120 and tc[1]<390:
            pyautogui.moveTo( 8 , 4*(tc[1]-120))
        elif tc[0]>590 and tc[1]>120 and tc[1]<390:
            pyautogui.moveTo(1912, 4*(tc[1]-120))
        elif tc[0]>110 and tc[0]<590 and tc[1]<120:
            pyautogui.moveTo(4*(tc[0]-110) , 8)
        elif tc[0]>110 and tc[0]<590 and tc[1]>390:
            pyautogui.moveTo(4*(tc[0]-110) , 1072)
        elif tc[0]<110 and tc[1]<120:
            pyautogui.moveTo(8, 8)
        elif tc[0]<110 and tc[1]>390:
            pyautogui.moveTo(8, 1072)
        elif tc[0]>590 and tc[1]>390:
            pyautogui.moveTo(1912, 1072)
        else:
            pyautogui.moveTo(1912, 8)
    elif action == 'left':
        pyautogui.click(button = 'left')
        time.sleep(0.1)
    elif action == 'right':
        pyautogui.click(button = 'right')
        time.sleep(0.1)
    elif action == 'scroll':            
        if (prevSc > tc[0]):
            pyautogui.scroll(-1)    #down scroll
        elif (prevSc < tc[0]):
            pyautogui.scroll(1)     #up scroll
        prevSc = tc[0]
        time.sleep(0.1)
    elif action == 'drag':
        pyautogui.mouseDown()
        global t_cen, blueRange, greenRange, redRange
        while(1):
            k = cv2.waitKey(1)
            #Check if key pressed is 'ESC' and breaks the loop
            if (k == 27):
                break
            
            _, frameinv = cap.read()
			# flip horizontaly to get mirror image in camera
            frame = cv2.flip( frameinv, 1)
            
            HSVImage = cv2.cvtColor( frame, cv2.COLOR_BGR2HSV)

            pt_pos = t_cen
            b_cen = trackFinger('T', blueRange, HSVImage)
            g_cen = trackFinger('I', greenRange, HSVImage)	
            r_cen = trackFinger('M', redRange, HSVImage)
            #draw centroid and line
            if (b_cen[0] != -1 and g_cen[0] != -1 and r_cen[0] != -1):
                #Show T,I,M tracking circle
                cv2.circle(frame, b_cen, 5, (255,0,0), -1)
                cv2.circle(frame, g_cen, 5, (0,255,0), -1)
                cv2.circle(frame, r_cen, 5, (0,0,255), -1)
                
                #line joining T,I,M
                cv2.line(frame, b_cen, g_cen, (255,0,0))
                cv2.line(frame, r_cen, g_cen, (255,0,0))
                
            if 	pt_pos[0]!=-1 and b_cen[0]!=-1:
                t_cen = setCursorPos(b_cen, pt_pos)

            performAction('move', t_cen, g_cen, r_cen)
            cv2.imshow('Test', frame)
            if chooseOption(t_cen, g_cen, r_cen) != 'drag':
                break
        pyautogui.mouseUp()

#Captures the video at camera 0
cap = cv2.VideoCapture(0)


#INFINITE LOOP
while(1):
    #STEP 1: Video capture in frames
    #single frame read from capture 'cap'
    _, frame = cap.read()
    #flip the frame
    flipped = cv2.flip(frame, 1) 
    
    #Flipped image to HSV_MODE
    HSVImage = cv2.cvtColor(flipped, cv2.COLOR_BGR2HSV)
    
    #Step 2: Calibration
    #Calibration window module
    if (flag):
        blueRange = calibrateFinger('T', blueRange) #calibrate thumb finger
        greenRange = calibrateFinger('I', greenRange) #calibrate index finger
        redRange = calibrateFinger('M', redRange) #calibrate middle finger
        flag = False #flag flase means completion of the calibration and not required next time
        
        
    pt_pos = t_cen #previous thumb position
    #Getting point of T,I,M
    centerThumb = trackFinger('T', blueRange, HSVImage)
    centerIndex = trackFinger('I', greenRange, HSVImage)
    centerMiddle = trackFinger('M', redRange, HSVImage)
    #draw centroid and line
    if (centerThumb[0] != -1 and centerIndex[0] != -1 and centerMiddle[0] != -1):
        #Show T,I,M tracking circle
        cv2.circle( flipped, centerThumb, 5, (255,0,0), -1)
        cv2.circle( flipped, centerIndex, 5, (0,255,0), -1)
        cv2.circle( flipped, centerMiddle, 5, (0,0,255), -1)
        
        #line joining T,I,M
        cv2.line(flipped, centerThumb, centerIndex, (255,0,0))
        cv2.line(flipped, centerMiddle, centerIndex, (255,0,0))
     
    if 	pt_pos[0]!=-1 and centerThumb[0]!=-1:
        t_cen = setCursorPos(centerThumb, pt_pos)
    
    action = chooseOption(t_cen,  centerIndex, centerMiddle)
    if (Simulate == True):
        if action != -1:
            performAction(action, t_cen, centerIndex, centerMiddle)
            cv2.imshow('Test', flipped)
    else:
        cv2.putText(flipped, str(action), (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), lineType=cv2.LINE_AA)
        cv2.imshow('Test', flipped)
    #Returns key press from keyboard 
    k = cv2.waitKey(1)
    
    #Check if key pressed is 'ESC' and breaks the loop
    if (k == 27):
        break
    elif (k == 32):
        cv2.destroyWindow('Test')
        flag = True
    elif (k == ord('y')):
        cv2.destroyWindow('Test')
        Simulate  = True
    elif (k == ord('n')):
        cv2.destroyWindow('Test')
        Simulate = False
cap.release()
cv2.destroyAllWindows()
	
		




