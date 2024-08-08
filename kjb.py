from picarx import Picarx
from time import sleep
import readchar
import threading
import socket
import cv2
import pickle
import struct
import sys
import numpy as np


class project:

    def __init__(self, px):

        # 소켓 생성
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 서버 주소
        self.server_address = ('172.20.25.42', 5555)

        # 캘리브레이션을 위한 모터값
        # 카메라 수평
        self.camera_head_horizontal = 0
        # 카메라 수직
        self.camera_head_vertical = 0
        # 바퀴
        self.motor = -8.0  

        # 이미지를 저장한 여부에 대한 변수 선언
        self.image_flag = False

        # 차량 할당
        self.px = px

        # AI로 인식한 헤더값을 저장하는 변수
        self.AI_header = None

        # 도로주행 자세제어에 대한 변수 선언
        self.control_picar = None

        # AI가 인식한 이미지 명령 수행 여부를 확인하는 변수 선언
        self.AI_flag = False

        # Picar-x가 정지선에서 AI 이미지 명령 수행 가능한 상태인지 확인하는 변수 선언
        self.stopline_flag = False

        # 데이터를 저장하는 변수 선언
        self.grayscale_value = True
        self.ultrasonic_value = None

        # 도로주행 판단수행 여부를 저장하는 변수 선언 - default : True
        self.grayscale_flag = True

        # 회피기동을 실행하는 거리 - default : 30 (Unit : cm)
        self.avoid_distance = 30
        # 회피기동을 수행함에 있어 필요한 회피각 - default : 30 (Unit : deg)
        self.avoid_angle = 30
        # 회피기동을 수행함에 있어 각속도에 따른 회피시간 - default : 3 (Unit : sec)
        self.avoid_time = 3

        # 이미지를 저장하는 변수
        self.image = None

        # Grayscale을 위한 참조변수
        self.reference = [500, 500, 500]

        # Picar-x 객체의 Lock
        self.picar_lock = threading.Lock()

        # cv2 객체 생성
        self.cap = cv2.VideoCapture(0)

        # 스레드
        t1 = threading.Thread(target=self.read_data)
        #t2 = threading.Thread(target=self.avoid_question)
        t4 = threading.Thread(target=self.send_data)

        t1.start()
        #t2.start()
        t4.start()

    # Grayscale에 맞는 데이터를 할당하는 함수
    def get_line_status(self):
        if self.grayscale_value[0] >= self.reference[0] and self.grayscale_value[1] >= self.reference[1] and self.grayscale_value[2] >= self.reference[2]:
            self.control_picar = 'back'
        elif self.grayscale_value[0] < self.reference[0] and self.grayscale_value[1] < self.reference[1] and self.grayscale_value[2] < self.reference[2]:
            self.control_picar = 'disconnected'
        elif self.grayscale_value[0] >= self.reference[0]:
            self.control_picar = 'right'
        elif self.grayscale_value[2] >= self.reference[2]:
            self.control_picar = 'left'
        else:
            self.control_picar = 'forward'

    # 캘리브레이션을 맞추는 함수
    def offset_picar(self):
        self.px.dir_servo_calibrate(self.camera_head_horizontal)
        self.px.cam_pan_servo_calibrate(self.motor)
        self.px.cam_tilt_servo_calibrate(self.camera_head_vertical)

    
    # 서버로 이미지를 전달하는 함수
    def send_data(self):
        try:
            self.client_socket.connect(self.server_address)

            t5 = threading.Thread(target=self.read_header)
            t5.start()

            while True:
                
                ret, self.image = self.cap.read()

                print(ret)
                print(self.image)
                if not ret:
                    continue


                _, image = cv2.imencode('.JPEG', self.image, [cv2.IMWRITE_JPEG_QUALITY, 90])
                frame_data = pickle.dumps(image)
                frame_size = len(frame_data)

                self.client_socket.sendall(frame_size.to_bytes(4, byteorder='big'))
                self.client_socket.sendall(frame_data)
                sleep(0.75)

        except Exception as e:
            print(e)
            sleep(0.1)

    # 서버로부터 헤더값을 받아오는 함수
    def read_header(self):
        while True:
            try:
                self.AI_header = int(self.client_socket.recv(1024).decode())

            except Exception as e:
                print(e)

    # Picar-X의 센서 데이터값을 받아오는 함수
    def read_data(self):
        while True:
            try:
                # 명도 값
                self.grayscale_value = px.get_grayscale_data()
                # 거리 값
                self.ultrasonic_value = round(px.ultrasonic.read(), 2)

                if self.grayscale_flag:
                    self.get_line_status()
                    if self.control_picar == 'disconnected':
                        self.AI_movement()
                    self.align_grayscale()

                print(f' grayscale : {self.grayscale_value} ultrasonic: {self.ultrasonic_value}')

                sleep(0.1)
            
            except Exception as e:
                print(e)
                sleep(0.1)

    # 헤더값에 맞는 기동을 수행하는 함수
    def align_grayscale(self):

        motor_run = False

        if self.control_picar == 'left':
            self.px.forward(15)
            self.px.cam_pan_servo_calibrate(self.motor+30)

        elif self.control_picar == 'right':
            self.px.forward(15)
            self.px.cam_pan_servo_calibrate(self.motor-30)
            
        elif self.control_picar == 'forward':
            self.offset_picar()
            self.px.forward(15)

        elif self.control_picar == 'back':
            if motor_run == False:
                motor_run = True
                self.px.forward(-30)
            else:
                motor_run = False
                self.px.stop()

    #AI 값을 보고 판단하는 함수
    def AI_movement(self):
        
        if self.AI_header == 0:
            self.offset_picar()
            self.px.forward(0)
        elif self.AI_header == 1:
            self.px.forward(10)
            self.px.cam_pan_servo_calibrate(self.motor+20)
        elif self.AI_header == 2:
            self.px.forward(10)
            self.px.cam_pan_servo_calibrate(-27)
        elif self.AI_header == 3:
            self.offset_picar()
            self.px.forward(0)
            sleep(2)
        while True:
            self.grayscale_value = px.get_grayscale_data()
            self.get_line_status()
            self.px.forward(10)
            print(self.control_picar)
            if self.control_picar != 'disconnected':
                break

    # 회피기동 여부를 판단하는 함수
    def avoid_question(self):
        if self.ultrasonic_value <= self.avoid_distance:
            self.avoid_move()

    # 회피기동을 수행하는 로직함수
    def avoid_move(self):
        while True:
            try:
                self.picar_lock.acquire()
                break
            except:
                sleep(0.1)

        # 회피기동시, 도로 폭(60cm) 차선 폭(15cm) 차량의 위치 - 차선의 중앙(7.5cm)를 기동에 사용
        px.forward(2.5)
        px.set_dir_servo_angle(self.avoid_angle)
        sleep(self.avoid_time)

        self.picar_lock.release()


if __name__ == '__main__':
    px = Picarx()
    a = project(px)
