from logging import error
import socket
import threading
from time import sleep

HOST = '26.176.221.42'
PORT = 5555
ADDR = (HOST, PORT)
FORMAT = 'UTF-8'
HEADER = 1024

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

server.listen()

nicknames = []
clients = []
def broadcast(msg):
    for client in clients:
        try:
            client.send(msg)
        except ConnectionResetError:
            continue
        except error as e:
            print(e)
            continue

def handle(client):
    broadcastMsgHistory(client)
    while True:
        try:
            msg = client.recv(1024).decode(FORMAT)
            if "483274874727234" in msg:
                broadcast(f"{nicknames[clients.index(client)]} se ha cambiado el nombre de usuario a '{msg.split(',')[1]}'.".encode(FORMAT))
                nicknames[clients.index(client)] = msg.split(',')[1]
            else:
                print(f"{nicknames[clients.index(client)]}: {msg}")
                broadcast(f"{nicknames[clients.index(client)]}: {msg.rstrip()}".encode(FORMAT))
                msgHistory.append(f"{nicknames[clients.index(client)]}: {msg.rstrip()}")
        except:
            broadcast(f"{nicknames[clients.index(client)]} se ha ido. Qué maricón.".encode(FORMAT))
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            nicknames.remove(nickname)
            break
    
    client.close()

def receive():
    while True:
        client, addr = server.accept()
        print(f"CONNECTED WITH {addr}.")
        
        client.send("NICK".encode(FORMAT))
        try:
            nickname = client.recv(HEADER).decode()

            nicknames.append(nickname)
            clients.append(client)

            print(f"NICKNAME'S CLIENT IS '{nickname}'.")
            broadcast(f"{nickname} se ha unido.".encode(FORMAT))

            thread1 = threading.Thread(target=handle, args=(client,))
            thread1.start()
        except ConnectionResetError:
            continue

msgHistory = []
def broadcastMsgHistory(client):
    for msg in msgHistory:
        client.send(msg.encode(FORMAT))
        sleep(0.001)

print("SERVER RUNNING.")
receive()