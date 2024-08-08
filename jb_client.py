import cv2
import pickle
import threading
import socket
from time import sleep

image_path = r"C:\Users\rlawk\OneDrive\Desktop\image.png"

image_i = cv2.imread(image_path)



client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_add = ('10.33.32.87', 5555)

# 서버로 이미지를 전달하는 함수
def send_data():
    try:
        client_socket.connect(server_add)

        t1 = threading.Thread(target=read_data)
        t1.start()

        while True:
            
            print('client 1')

            image = cv2.imencode('.JPG', image_i)
            frame_data = pickle.dumps(image)
            frame_size = len(frame_data)

            print('client 2')

            client_socket.sendall(frame_size.to_bytes(4, byteorder='big'))
            print(frame_size)
            print('client 3')
            client_socket.sendall(frame_data)
            print('client 4')
            sleep(0.1)

    except Exception as e:
        print(e)

def read_data():
    while True:
        try:
            data = client_socket.recv(1024).decode()
            print(data)

        except Exception as e:
            print(e)
    
if __name__ == '__main__':
    send_data()