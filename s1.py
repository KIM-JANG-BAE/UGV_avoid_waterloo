# Receives images and runs them through ML algorithm

import socket
import struct
import cv2
import pickle
from time import sleep
# for demonstration
import matplotlib.pyplot as plt

HOST = '0.0.0.0'
PORT = 5555

flag = True
i = 0

def show_image(frame):
    global i
    path  = "C:\\Users\\rlawk\\OneDrive\\Desktop\\coco\\image" + str(i) + ".jpg"

    with open(path, 'wb') as f:
        f.write(frame)
    print('save')

    i += 1
    i = i % 50
    print(f'i = {i}')

def send_data(socket, frame):
    s = '2'
    s = s.encode()
    socket.send(s)
    

def main():
    global flag
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    print("Server started")
    while True:
        client_socket, addr = s.accept()
        print("Connected by", addr)

        try: 
            while True:
                print('server 1')
                frame_size_bytes = client_socket.recv(4)
                frame_size = int.from_bytes(frame_size_bytes, byteorder='big')

                print(frame_size)

                print('server 2')
                if frame_size == 0:
                    continue
                
                data = b''
                while len(data) < frame_size:
                    recv = client_socket.recv(4096)
                    if not recv:
                        break
                    data += recv

                print('server 3')

                frame = pickle.loads(data)
                
                print(frame)

                print('server 4')
                
                show_image(frame)

                print('server 5')
                send_data(client_socket, frame)

                frame_size = 0

        except Exception as e:
            print(e)
        finally:
            client_socket.close()

if __name__ == "__main__":
    main()
