import socket
import threading
from time import sleep
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog
from pygetwindow import getActiveWindowTitle
from playsound import playsound
from sys import path
from pickle import dumps, loads

DIRECT = path[0]
HOST = '26.176.221.42'
PORT = 5555
HEADER = 8192
VERSION = "1.0.3"

class Client():
    def __init__(self, host, port):
        self.play_sound = False
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.addr)

        msg = tkinter.Tk()
        msg.withdraw()
        msg.resizable(False, False)

        self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)[:15]

        self.gui_done = False
        self.running = True
        
        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)
        self.lock = threading.Lock()
        self.notification_thread = threading.Thread(target=self.notification)
        self.notification_thread.start()
        gui_thread.start()
        receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title(f"NotDiscord v{VERSION}")
        self.win.configure(bg="lightgray")
        self.win.resizable(False, False)
        self.win.geometry("860x560")

        self.frame = tkinter.Frame(self.win)
        
        self.users_connected = tkinter.Text(self.frame, height=24, width=21, wrap='word')
        self.users_connected.pack(side=tkinter.LEFT,expand=True)
        self.users_connected.config(state="disabled")
        sb = tkinter.Scrollbar(self.frame)
        sb.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)

        self.users_connected.config(yscrollcommand=sb.set)
        sb.config(command=self.users_connected.yview)
        self.frame.grid(row=1, column=2)

        self.chat_label = tkinter.Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.grid(row=0, column=0)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.grid(row=1, column=0)
        self.text_area.config(state="disabled")

        self.msg_label = tkinter.Label(self.win, text="Mensaje:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.grid(row=2, column=0)

        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.grid(row=3, column=0)

        self.send_button = tkinter.Button(self.win, text="Enviar", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.grid(row=4, column=0)
        self.win.bind('<Return>', lambda event=None: self.send_button.invoke())

        self.change_nick_button = tkinter.Button(self.win, text="Cambiar usuario", command=self.changeNick)
        self.change_nick_button.config(font=("Arial", 12))
        self.change_nick_button.grid(row=5, column=0)

        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def changeNick(self):
        msg = tkinter.Tk()
        msg.withdraw()
        msg.resizable(False, False)

        oldNickname = self.nickname
        self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)
        if self.nickname == None:
            self.nickname = oldNickname
        else:
            self.sock.send(dumps(f"483274874727234,{self.nickname[:20]}"))

    def write(self):
        msg = f"{self.input_area.get('1.0', 'end')}"
        if len(msg.strip()) > 0:
            self.sock.send(dumps(msg[:400]))
            self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

    def notification(self):
        while True:
            self.lock.acquire()
            playsound(f'{DIRECT}\extras\c.mp3')
            
    def receive(self):
        while self.running:
            try:
                msg = loads(self.sock.recv(HEADER))
                if msg == "NICK":
                    self.sock.send(dumps(self.nickname))
                elif self.gui_done:
                    if type(msg) != list:
                        if len(msg.strip()) > 0:
                            if "NotDiscord" in getActiveWindowTitle():
                                pass
                            else:
                                self.lock.release()
                            self.text_area.config(state="normal")
                            self.text_area.insert("end", f"{msg}\n")
                            self.text_area.yview("end")
                            self.text_area.config(state="disabled")
                    else:
                        self.users_connected.config(state="normal")
                        self.users_connected.delete('1.0', 'end')
                        self.users_connected.config(state="disabled")
                        for user in msg:
                            self.users_connected.config(state="normal")
                            self.users_connected.insert("end", f"{user}\n")
                            self.users_connected.yview("end")
                            self.users_connected.config(state="disabled")
            except ConnectionAbortedError:
                break
            #except:
            #    print("I don't know.")
            #    self.sock.close()
            #    break

client = Client(HOST, PORT)