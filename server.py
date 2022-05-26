from logging import error
import socket
import threading
from time import sleep
from pickle import dumps, loads

HOST = '26.176.221.42'
PORT = 5555
ADDR = (HOST, PORT)
HEADER = 8192*2

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()

nicknames = []
clients = []
filesUploaded = []
def broadcast(msg):
    for client in clients:
        try:
            client.send(dumps(msg))
        except ConnectionResetError:
            continue
        except error as e:
            print(e)
            continue

def handle(client):
    broadcastMsgHistory(client)
    sleep(0.4)
    while True:
        try:
            broadcastUsersConnected()
            sleep(0.4)
            broadcast([filesUploaded, "Upload", "History"])
            msg = loads(client.recv(HEADER))
            if type(msg) == str:
                if "483274874727234" in msg:
                    broadcast(f"{nicknames[clients.index(client)]} se ha cambiado el nombre de usuario a '{msg.split(',')[1]}'.")
                    nicknames[clients.index(client)] = msg.split(',')[1]
                else:
                    print(f"{nicknames[clients.index(client)]}: {msg.strip()}")
                    broadcast(f"{nicknames[clients.index(client)]}: {msg.strip()}")
                    msgHistory.append(f"{nicknames[clients.index(client)]}: {msg.strip()}")
            else:
                print(f"{msg[0], msg[2]}")
                filesUploaded.append([msg[0], msg[2], msg[3]])
                broadcast([filesUploaded, "Upload", ""])
        except ConnectionResetError or EOFError:
            broadcast(f"{nicknames[clients.index(client)]} se ha ido. Qué maricón.")
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            nicknames.remove(nickname)
            broadcastUsersConnected()
            break
    
    client.close()

def receive():
    while True:
        client, addr = server.accept()
        print(f"CONNECTED WITH {addr}.")
        
        client.send(dumps("NICK"))
        try:
            nickname = loads(client.recv(HEADER))

            nicknames.append(nickname)
            clients.append(client)
            print(f"NICKNAME'S CLIENT IS '{nickname}'.")
            broadcast(f"{nickname} se ha unido.")

            thread1 = threading.Thread(target=handle, args=(client,))
            thread1.start()
        except ConnectionResetError:
            continue

msgHistory = []
def broadcastMsgHistory(client):
    try:
        client.send(dumps([msgHistory, "msgHistory"]))
    except ConnectionAbortedError:
        pass

def broadcastUsersConnected():
    for client in clients:
        try:
            client.send(dumps([nicknames, "nicknames"]))
        except ConnectionResetError:
            break

print("SERVER RUNNING.")
receive()