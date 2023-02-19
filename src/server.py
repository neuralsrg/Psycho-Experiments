import socket
import os
import glob
import pandas as pd


cfg = pd.read_csv(os.path.join(".", "src", "socket_config.csv"))
IP, PORT = cfg.ip[0], cfg.port[0]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))

print('Listening...')
server.listen(1)
incoming_socket, addr = server.accept()
print(f'Incoming transmission from {addr}')

while True:
    message = incoming_socket.recv(1024).decode('utf-8')
    if not message:
        incoming_socket.close()
        print(f'[{addr}] Left the session')
        break

    print(f'[{addr}] {message}')