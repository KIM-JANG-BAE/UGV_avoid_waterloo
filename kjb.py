from picarx import Picarx
from time import sleep
import readchar
import threading
import socket
import cv2
import pickle
import struct

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

        # 차량 할당
        self.px = px

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


        # 라즈베리파이 ip, port
        self.client_ip = '172.20.25.30'
        self.client_port = 5555

        # 스레드
        t1 = threading.Thread(target=self.read_data)
        #t2 = threading.Thread(target=self.avoid_question)
        t3 = threading.Thread(target=self.gray_question)
        t4 = threading.Thread(target=self.send_data)


        t1.start()
        #t2.start()
        t3.start()
        t4.start()

    # Grayscale에 맞는 데이터를 할당하는 함수
    def get_line_status(self):
        if self.grayscale_value[0] > self.reference[0] and self.grayscale_value[1] > self.reference[1] and self.grayscale_value[2] > self.reference[2]:
            self.control_picar = 'back'

        elif self.grayscale_value[1] >= self.reference[1]:
            self.control_picar = 'forward'

        elif self.grayscale_value[0] >= self.reference[0]:
            self.control_picar = 'right'

        elif self.grayscale_value[2] >= self.reference[2]:
            self.control_picar = 'left'

        else:
            self.control_picar = 'forward'

    # 캘리브레이션을 맞추는 함수
    def offset_picar(self):
        self.dir_servo_calibrate(self.camera_head_horizontal)
        self.cam_pan_servo_calibrate(self.motor)
        self.cam_tilt_servo_calibrate(self.camera_head_vertical)

    # 서버에서 사인에 맞는 명령제어값을 받는 함수
    def receive_header(self):
        pass

    # 서버로 이미지를 전달하는 함수
    def send_data(self):
        try:
            self.client_socket.connect(self.server_address)

            while True:
                
                image = pickle.dumps(self.image)
                image_size = struct.pack('L', len(image))
                socket.sendall(image_size + image)

                data = b''
                payload_size = struct.calcsize('L')
                

                self.client_socket.send()

        except:
            pass

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
                    self.align_grayscale()

                print(f' grayscale : {self.grayscale_value} ultrasonic: {self.ultrasonic_value}')

                sleep(0.1)
            
            except:
                print('Lock is already acquired')
                sleep(0.1)

    # 헤더값에 맞는 기동을 수행하는 함수
    def align_grayscale(self):

        motor_run = False

        if self.control_picar == 'left':
            self.px.forward(5)
            self.px.cam_pan_servo_calibrate(self.motor+30)

        elif self.control_picar == 'right':
            self.px.forward(5)
            self.px.cam_pan_servo_calibrate(self.motor-30)
            
        elif self.control_picar == 'forward':
            self.offset_picar()
            self.px.forward(10)

        elif self.control_picar == 'back':
            if motor_run == False:
                motor_run = True
                self.px.forward(-30)
            else:
                motor_run = False
                self.px.stop()


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
