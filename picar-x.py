from time import sleep
import readchar #입력키 받아오기
import threading
import sys
import numpy as np
import datetime
import socket
import cv2 as cv
from vilib import vilib

path = f"HAM/Pictures/picar-x/" # 사진 저장 위치

from picarx import Picarx

####################### 오프셋 ########################
ai_answer = 0
da = 0
va = -8.0
mo = 0
######################################################

####################### 소켓통신 ######################
HOST = ''
PORT = 0
######################################################

####################### 센서값 제어 ###################
reference = [500, 500, 500] # 기준값
SafeDistance = 40   # > 40 safe
DangerDistance = 20 # > 20 && < 40 turn around,
                    # < 20 backward
ref = 500
######################################################

px = Picarx()

def offset_s():# 초기 값
    px.dir_servo_calibrate(da)
    px.cam_pan_servo_calibrate(va)
    px.cam_tilt_servo_calibrate(mo)

def line_following():#라인 따라가기
    global reference
    motor_run = False
    while True:
        gm_val_list = px.get_grayscale_data()
        re = get_line_status(gm_val_list)
        print(re)
        if re == 'forward':
            offset_s()
            px.forward(10)
        elif re == 'right':
            px.forward(5)
            px.cam_pan_servo_calibrate(va-30)
        elif re == 'left':
            px.forward(5)
            px.cam_pan_servo_calibrate(va+30)
        elif re == 'back':
            if motor_run == False:
                motor_run = True
                px.forward(-30)
            else:
                motor_run = False
                px.stop()

def get_line_status(fl_list):
    global reference
    if fl_list[0] > reference[0] and fl_list[1] > reference[1] and fl_list[2] > reference[2]:
        return 'back'

    elif fl_list[1] >= reference[1]:
        return 'forward'

    elif fl_list[0] >= reference[0]:
        return 'right'

    elif fl_list[2] >= reference[2]:
        return 'left'

    else:
        return 'forward'

# def set_references(references): #기준값 잡기
#     global reference
#     if isinstance(references, int) or isinstance(references, float):
#         reference = [references] * 3
#     elif isinstance(references, list) and len(references) != 3:
#         reference = references
#     else:
#         raise TypeError("reference parameter must be \'int\', \'float\', or 1*3 list.")


def obstacle_avoid():#장애물 감지
    distance = round(px.ultrasonic.read(), 2) #초음파 센서 감지
    if distance >= SafeDistance:
        return 0 #forward = 0
    elif distance >= DangerDistance:
        return 1 # right = 1
    else:
        return 2 # left = 2

def stops(): # 멈추기
    px.stop()

def direction(obs): #방향 전환
    global ai_answer
    ai_answer = 0
    if obs == 0 and ai_answer == 0:
        offset_s()
        px.forward(50)
    else: # 우선순위 장애물 > ai
        if obs == 1:
            px.forward(5)
            px.cam_pan_servo_calibrate(va+30)
        elif obs == 2:
            px.forward(5)
            px.cam_pan_servo_calibrate(va-30)
        elif ai_answer == 1:
           px.forward(5)
           px.cam_pan_servo_calibrate(va+10)
        elif ai_answer == 2:
           px.forward(5)
           px.cam_pan_servo_calibrate(va-10)
        else:
            px.stop()
    sleep(1)

def AI_response():
    while True:
        global ai_answer # ai 에서 받은 값 저장

def main_loop():
    while True:
        global ai_answer
        obs = obstacle_avoid()
        direction(obs)
#################################카메라###################################
# def AI_camera_main():
#     cap = cv.VideoCapture(0)
#     while True:
#         now = datetime.datetime.now()
#         filename = now.strftime('%Y-%m-%d-%H-%M-%S')+'.jpg'
#         vilib.take_phote(path, filename)
#         ret, frame = cap.read()
#         if ret == True:
#             cv.imwrite(filename', frame)

def AI_camera_main():
    cap = cv.VideoCapture(0)
    while True:
        now = datetime.datetime.now()
        filename = now.strftime('%Y-%m-%d-%H-%M-%S')+'.jpg'
        # vilib.take_phote(path, filename)
        # ret, frame = cap.read()
        # if ret == True:
        cv.imwrite(filename, frame)
        #     cv.imshow('frame', traitement(frame))
        # else:
        #     break
    # cap.release()
    # cv.destroyAllWindows()

# def traitement(frame):
#     ligne = 400
#     img = prepareImg(frame)
#     img = reduirBruit(img)
#     mean = meanImg(img)
#     mask = maskImg(img)
#     seuillage = seuilImg(img, mean, mask)
#     direction, valeurRoutation = autoCorrection(seuillage, ligne=ligne)
#     angle = np.arccos(valeurRoutation/(img.shape[0]-ligne))*180/np.pi
#     if direction == 0:
#         offset_s()
#         px.forward(5)
#     elif direction == 1:
#         px.forward(5)
#         px.cam_pan_servo_calibrate(va-angle)
#     elif direction == 2:
#         px.forward(5)
#         px.cam_pan_servo_calibrate(va+angle)
#     else:
#         offset_s()
#         px.forward(5)
#     contourImg = contour(frame, seuillage)
#     return contourImg

# def contour(fram, newImg):
#     contours, hierarchy = cv.findContours(image=newImg, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_NONE)
#     image_draw = fram.copy()
#     cv.drawContours(image=image_draw, contours=contours, contourIdx=-1, color=(0, 0, 0), thickness=5, lineType=cv.LINE_AA)
#     return image_draw

# def autoCorrection(newImg, axe=460, ligne=400):
#     disGauche, disDroit, direction, valeurRoutation = 0, 0, 0, 0
#     m = (np.where(newImg[ligne,:]==255)) # 255는 횐색의 픽셀값
#     pose = [ (m[0][i],m[0][i-1]) for i in range(len(m[0])) if m[0][i]-m[0][i-1]>300]
#     if len(pose)==1:
#         disDroit = np.abs(pose[0][0]-axe)
#         disGauche = np.abs(pose[0][1]-axe)
#         if disGauche > disDroit:
#             direction, valeurRoutation = -1, np.abs(disDroit-disGauche)
#         elif disDroit > disGauche:
#             direction, valeurRoutation = 1, np.abs(disDroit-disGauche)
#         else:
#             direction, valeurRoutation = 0, np.abs(disDroit-disGauche)
#         print(disDroit)
        
#     return direction, valeurRoutation


# def prepareImg(fram):
#     img = cv.cvtColor(fram, cv.COLOR_BGR2GRAY)
#     img = np.array(img)
#     return img

# def reduirBruit(img):
#     return cv.bilateralFilter(img, 5, 50, 50)

# def seuilImg(img, mean, masked_img):
#     img = cv.split(img)[0]
#     (_, newImg) = cv.threshold(masked_img, mean + 55, 255, cv.THRESH_BINARY)
#     return newImg

# def meanImg(img):
#     means, _ = cv.meanStdDev(img)
#     return int(means[0][0])

# def mask(img, v):
#     mask = np.zeros_like(img)
#     chaine_count = 1
#     match_mask_color = (255,) * chaine_count
#     cv.fillPoly(mask, v, match_mask_color)
#     mask_img = cv.bitwise_and(img, mask)
#     return mask_img

# def maskImg(img):
#     v = [(-50, img.shape[0]), (img.shape[1]/2-60, img.shape[0]/1.6-30), (img.shape[1]/2+20, img.shape[0]/1.6-30), (img.shape[1]+50, img.shape[0])]
#     return mask(img, np.array([v], np.int32),)

##########################################################################
def socket_main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def main():# 메인
    global stop_thread
    print("start : w , stop : s")
    while True:
        key = readchar.readkey()
        key = key.lower()
        if key in('w', 's'):
            if 'w' == key:
                #t1 = threading.Thread(socket_main())
                #t1.start()
                offset_s()
                #t2 = threading.Thread(target=main_loop)
                #t2.start()
                #t3 = threading.Thread(target=line_following)  #라인
                #t3.start()
                print(3)
                #t4 = threading.Thread(AI_camera_main())
                #t4.start()
                while True:
                    if readchar.readkey().lower() == 's':
                        stop_thread = True
                        stops()
                        offset_s()
                        #t1.join()
                        #t2.join()
                        #t3.join()
                        #t4.join()
                        break

if __name__=="__main__":
    main()