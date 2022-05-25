from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
from tkinter import Tk, Text, Label, Button, simpledialog
from tkinter.scrolledtext import ScrolledText
from _tkinter import TclError
from pygetwindow import getActiveWindowTitle
from playsound import playsound
from sys import path
from pickle import dumps, loads
from time import sleep

DIRECT = path[0]
HOST = '26.176.221.42'
PORT = 5555
HEADER = 8192*2
VERSION = "1.0.4"

class Client():
    def __init__(self, host, port):
        self.BGCOLOR = "white"
        self.USERS_CONNECTED = 0

        self.reconnect_again = True

        self.host = host
        self.port = port
        try:
            self.addr = (host, port)
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(self.addr)
            self.connected = True
        except ConnectionRefusedError:
            print("Can't connect, retry later.")
            self.connected = False

        msg = Tk()
        msg.withdraw()
        msg.resizable(False, False)

        self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)[:20]

        self.gui_done = False
        self.running = True
        
        gui_thread = Thread(target=self.gui_loop)
        self.receive_thread = Thread(target=self.receive)
        self.lock = Lock()
        self.notification_thread = Thread(target=self.notification)
        
        self.notification_thread.start()
        gui_thread.start()
        self.receive_thread.start()

    def gui_loop(self):
        self.win = Tk()
        self.win.title(f"NotDiscord v{VERSION}")
        self.win.configure(bg="lightgray")
        self.win.resizable(False, False)
        self.win.geometry("860x560")

        self.chat_label = Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.grid(row=0, column=0)

        self.text_area = ScrolledText(self.win, bg=self.BGCOLOR)
        self.text_area.grid(row=1, column=0)
        self.text_area.config(state="disabled")

        self.msg_label = Label(self.win, text="Mensaje:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.grid(row=2, column=0)

        self.input_area = Text(self.win, height=3)
        self.input_area.grid(row=3, column=0)

        self.send_button = Button(self.win, text="Enviar", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.grid(row=4, column=0)
        self.win.bind('<Return>', lambda event=None: self.send_button.invoke())

        self.change_nick_button = Button(self.win, text="Cambiar usuario", command=self.changeNick)
        self.change_nick_button.config(font=("Arial", 12))
        self.change_nick_button.grid(row=5, column=0)

        self.chat_label = Label(self.win, text=f"Usuarios conectados ({self.USERS_CONNECTED})", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.grid(row=0, column=1)

        self.users_connected = ScrolledText(self.win, bg="white", height=24, width=21)
        self.users_connected.grid(row=1, column=1)
        self.users_connected.config(state="disabled")

        self.reconnect_button = Button(self.win, text="Reconectar", command=self.reconnect)
        self.reconnect_button.config(font=("Arial", 12))
        self.reconnect_button.grid(row=3, column=1)

        self.reconnect_button = Button(self.win, text="Cambiar color (BG)", command=self.changeColor)
        self.reconnect_button.config(font=("Arial", 12))
        self.reconnect_button.grid(row=4, column=1)

        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def changeNick(self):
        if self.connected:
            msg = Tk()
            msg.withdraw()
            msg.resizable(False, False)

            oldNickname = self.nickname
            self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)
            if self.nickname == None:
                self.nickname = oldNickname
            else:
                self.sock.send(dumps(f"483274874727234,{self.nickname[:20]}"))

    def changeColor(self):
        msg = Tk()
        msg.withdraw()
        msg.resizable(False, False)

        oldColor = self.BGCOLOR
        self.BGCOLOR = simpledialog.askstring("Color", "Elige un color.", parent=msg)

        self.text_area.config(state="normal")
        try:
            self.text_area.config(bg=self.BGCOLOR)
        except TclError:
            self.BGCOLOR = oldColor
        self.text_area.config(state="disabled")

    def write(self):
        msg = f"{self.input_area.get('1.0', 'end')}"
        if len(msg.strip()) > 0:
            try:
                self.sock.send(dumps(msg[:400]))
            except OSError:
                self.writeInChat(f"ERROR AL ENVIAR EL MENSAJE. INTENTA RECONECTAR.")
                self.connected = False
            self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

    def notification(self):
        while True:
            self.lock.acquire()
            playsound(f'{DIRECT}\extras\c.mp3'.replace('base_library.zip\extras\c.mp3','extras\c.mp3'))

    def writeInChat(self, msg):
        self.text_area.config(state="normal")
        self.text_area.insert("end", f"{msg}\n")
        self.text_area.yview("end")
        self.text_area.config(state="disabled")

    def receive(self):
        while self.running:
            if self.connected and self.gui_done:
                try:
                    msg = loads(self.sock.recv(HEADER))
                    if msg == "NICK":
                        self.sock.send(dumps(self.nickname))
                    elif type(msg) == str:
                        if len(msg.strip()) > 0:
                            if "NotDiscord" in getActiveWindowTitle():
                                pass
                            else:
                                try:
                                    self.lock.release()
                                except RuntimeError:
                                    pass

                            self.text_area.config(state="normal")
                            self.text_area.insert("end", f"{msg}\n")
                            self.text_area.yview("end")
                            self.text_area.config(state="disabled")
                    elif type(msg) == list:
                        if msg[1] == "msgHistory":
                            self.text_area.config(state="normal")
                            for m in msg[0]:
                                self.text_area.insert("end", f"{m}\n")
                                self.text_area.yview("end")
                            self.text_area.config(state="disabled")
                        if msg[1] == "nicknames":
                            self.USERS_CONNECTED = len(msg[0])
                            self.chat_label.config(text=f"Usuarios conectados ({self.USERS_CONNECTED})")
                            self.users_connected.config(state="normal")
                            self.users_connected.delete('1.0', 'end')
                            for user in msg[0]:
                                self.users_connected.insert("end", f"{user}\n")
                                self.users_connected.yview("end")
                            self.users_connected.config(state="disabled")
                except ConnectionAbortedError:
                    break
                except ConnectionResetError:
                    self.writeInChat(f"ERROR DE CONEXIÓN. INTENTA RECONECTAR.")
                    self.connected = False
            else:
                sleep(.5)

    def reconnect(self):
        if not self.connected and self.reconnect_again:
            self.reconnect_again = False
            self.writeInChat(f"RECONECTANDO A '{HOST}'...")
            try:
                self.addr = (self.host, self.port)
                self.sock = socket(AF_INET, SOCK_STREAM)
                self.sock.connect(self.addr)
                self.connected = True
                self.text_area.config(state="normal")
                self.text_area.delete('1.0', 'end')
                self.text_area.config(state="disabled")
                self.writeInChat(f"CONEXIÓN ESTABLECIDA.")
                self.reconnect_again = True
            except ConnectionRefusedError:
                print("Can't connect, retry later.")
                self.connected = False
                self.writeInChat(f"ERROR AL CONECTAR.")
                self.reconnect_again = True

client = Client(HOST, PORT)