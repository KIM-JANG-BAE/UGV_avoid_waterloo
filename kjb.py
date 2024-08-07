from picarx import Picarx
from time import sleep
import readchar
import threading
import socket

class project:

    def __init__(self, px):

        print('1')

        # 소켓 생성
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print('2')

        # 서버 주소
        self.server_address = ('172.20.25.42', 5555)

        print('3')

        # 차량 할당
        self.px = px
        print('4')

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

        # Picar-x 객체의 Lock
        self.picar_lock = threading.Lock()

        # 라즈베리파이 ip, port
        self.client_ip = '172.20.25.30'
        self.client_port = 5555

        print('1')

        # 스레드
        t1 = threading.Thread(target=self.read_data)
        #t2 = threading.Thread(target=self.avoid_question)
        t3 = threading.Thread(target=self.gray_question)
        t4 = threading.Thread(target=self.send_data)


        t1.start()
        #t2.start()
        t3.start()
        t4.start()

    def receive_header(self):
        pass

    def send_data(self):
        print('2')
        try:
            self.client_socket.connect(self.server_address)

            while True:
                s = 'Hello'
                self.client_socket.send(s.encode())

        except:
            pass

    def read_data(self):
        while True:
            # Lock 획득
            while True:
                try:
                    self.picar_lock.acquire()
                    break
                except:
                    sleep(0.1)


            # 명도 값
            self.grayscale_value = px.get_grayscale_data()
            # 거리 값
            self.ultrasonic_value = round(px.ultrasonic.read(), 2)

            # 명도 값을 이용하여 해당 도로주행이 잘이루어지는지, 또한 그렇지 않은 경우 자세제어를 위한 헤더 설정
            # if self.grayscale_value

            print(f' grayscale : {self.grayscale_value} ultrasonic: {self.ultrasonic_value}')

            # Lock 해제
            self.picar_lock.release()
            sleep(0.1)


    def align_grayscale(self):
        while True:
            try:
                self.picar_lock.acquire()
                break
            except:
                sleep(0.1)

        self.grayscale_flag = False

        if self.control_picar == 'left':
            pass


        elif self.control_picar == 'right':
            pass

        print('gi')
        sleep(5)

        self.picar_lock.release()

    # 도로 주행이 잘 수행되는지 판단하는 함수
    def gray_question(self):
        if self.grayscale_value and self.grayscale_flag:
            self.align_grayscale()


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