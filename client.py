from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
from tkinter import Tk, Text, Label, Button, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter.scrolledtext import ScrolledText
from _tkinter import TclError
from pygetwindow import getActiveWindowTitle
from playsound import playsound
from sys import path
from pickle import dumps, loads
from time import sleep
from os.path import getsize

DIRECT = path[0]
HOST = '26.176.221.42'
PORT = 5555
HEADER = 8192*2
VERSION = "1.0.5"

class Client():
    def __init__(self, host, port):
        self.BGCOLOR = "white"
        self.USERS_CONNECTED = 0

        self.reconnect_again = True
        self.colorMode = True

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
        self.win = TkinterDnD.Tk()
        self.win.title(f"NotDiscord v{VERSION}")
        self.win.configure(bg="lightgray")
        self.win.resizable(False, False)

        self.files_label = Label(self.win, text="Archivos subidos (0)", bg="lightgray")
        self.files_label.config(font=("Arial", 15))
        self.files_label.grid(row=0, column=0)

        self.files_uploaded = ScrolledText(self.win, bg="white", height=24, width=21)
        self.files_uploaded.grid(row=1, column=0)
        self.files_uploaded.config(font=("Arial", "15"))
        self.files_uploaded.config(state="disabled")

        self.chat_label = Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 15))
        self.chat_label.grid(row=0, column=1)

        self.text_area = ScrolledText(self.win, bg=self.BGCOLOR)
        self.text_area.grid(row=1, column=1)
        self.text_area.drop_target_register(DND_FILES)
        self.text_area.dnd_bind("<<Drop>>", self.uploadFile)
        self.text_area.config(font=("Arial", "15"))
        self.text_area.config(state="disabled")
        
        self.msg_label = Label(self.win, text="Mensaje:", bg="lightgray")
        self.msg_label.config(font=("Arial", 15))
        self.msg_label.grid(row=2, column=1)

        self.input_area = Text(self.win, height=3)
        self.input_area.config(font=("Arial", 15))
        self.input_area.grid(row=3, column=1)

        self.send_button = Button(self.win, text="Enviar", command=self.write)
        self.send_button.config(font=("Arial", 15))
        #self.send_button.grid(row=4, column=0)
        self.win.bind('<Return>', lambda event=None: self.send_button.invoke())

        self.change_nick_button = Button(self.win, text="Cambiar usuario", command=self.changeNick)
        self.change_nick_button.config(font=("Arial", 15))
        self.change_nick_button.grid(row=5, column=1)

        self.users_connected_label = Label(self.win, text=f"Usuarios conectados ({self.USERS_CONNECTED})", bg="lightgray")
        self.users_connected_label.config(font=("Arial", 15))
        self.users_connected_label.grid(row=0, column=2)

        self.users_connected = ScrolledText(self.win, bg="white", height=24, width=21)
        self.users_connected.grid(row=1, column=2)
        self.users_connected.config(font=("Arial", 15))
        self.users_connected.config(state="disabled")

        self.reconnect_button = Button(self.win, text="Reconectar", command=self.reconnect)
        self.reconnect_button.config(font=("Arial", 15))
        self.reconnect_button.grid(row=3, column=2)

        self.change_color_button = Button(self.win, text="Cambiar color (BG)", command=self.changeColor)
        self.change_color_button.config(font=("Arial", 15))
        self.change_color_button.grid(row=4, column=2)

        self.change_color_mode_button = Button(self.win, text="Light/Dark", command=self.changeColorMode)
        self.change_color_mode_button.config(font=("Arial", 15))
        self.change_color_mode_button.grid(row=5, column=2)

        self.win.update()
        self.width = 0
        for widget in [
            self.files_uploaded,
            self.files_uploaded.vbar,
            self.text_area,
            self.text_area.vbar,
            self.users_connected,
            self.users_connected.vbar]:
            self.width += widget.winfo_width()

        self.height = 0
        for widget in [
            self.chat_label,
            self.text_area,
            self.msg_label,
            self.input_area,
            self.change_color_button,
            self.change_color_mode_button]:
            self.height += widget.winfo_height()
    
        self.win.geometry(f"{self.width}x{self.height}")

        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def uploadFile(self, event):
        file_size = getsize(event.data[1:-1])
        msg = [f"{self.nickname} está subiendo el archivo {event.data.split('/')[-1].replace('}', '')}", "Upload", file_size, self.nickname]
        try:
            self.sock.send(dumps(msg))
        except OSError:
            self.writeInChat(f"ERROR AL ENVIAR EL ARCHIVO. INTENTA RECONECTAR.")
            self.connected = False

    def changeNick(self):
        if self.connected:
            msg = Tk()
            msg.withdraw()
            msg.resizable(False, False)

            old_nickname = self.nickname
            self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)
            if self.nickname == None:
                self.nickname = old_nickname
            else:
                self.sock.send(dumps(f"483274874727234,{self.nickname[:20]}"))

    def changeColor(self):
        msg = Tk()
        msg.withdraw()
        msg.resizable(False, False)

        old_color = self.BGCOLOR
        self.BGCOLOR = simpledialog.askstring("Color", "Elige un color.", parent=msg)

        self.text_area.config(state="normal")
        try:
            self.text_area.config(bg=self.BGCOLOR)
        except TclError:
            self.BGCOLOR = old_color
        self.text_area.config(state="disabled")

    def changeColorMode(self):
        if self.colorMode:
            # DARK.
            bg = "#272727"
            fg = "white"
            bg2 = "#3f3d3d"
            self.colorMode = False
        else:
            # LIGHT.
            bg = "lightgray"
            fg = "black"
            bg2 = "white"
            self.colorMode = True

        self.win.configure(bg=bg)
        self.files_label.config(bg=bg, fg=fg)
        self.files_uploaded.config(bg=bg2, fg=fg)
        self.chat_label.config(bg=bg, fg=fg)
        self.text_area.config(bg=bg2, fg=fg)
        self.msg_label.config(bg=bg, fg=fg)
        self.input_area.config(bg=bg2, fg=fg)
        self.change_nick_button.config(bg=bg2, fg=fg)
        self.users_connected_label.config(bg=bg, fg=fg)
        self.users_connected.config(bg=bg2, fg=fg)
        self.reconnect_button.config(bg=bg2, fg=fg)
        self.change_color_button.config(bg=bg2, fg=fg)
        self.change_color_mode_button.config(bg=bg2, fg=fg)
    
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
                        elif msg[1] == "nicknames":
                            self.USERS_CONNECTED = len(msg[0])
                            self.users_connected_label.config(text=f"Usuarios conectados ({self.USERS_CONNECTED})")
                            self.users_connected.config(state="normal")
                            self.users_connected.delete('1.0', 'end')
                            for user in msg[0]:
                                self.users_connected.insert("end", f"{user}\n")
                                self.users_connected.yview("end")

                            self.users_connected.config(state="disabled")
                        elif msg[1] == "Upload":
                            if msg[2] != "History":
                                self.writeInChat(msg[0][-1][0])

                            filesUploaded = len(msg[0])
                            self.files_label.config(text=f"Archivos subidos ({filesUploaded})")
                            self.files_uploaded.config(state="normal")
                            self.files_uploaded.delete('1.0', 'end')
                            for file in msg[0]:
                                if file[1] >= 1024:
                                    self.files_uploaded.insert("end", f"{file[0].replace(f'{file[2]} está subiendo el archivo ', '')} ({round(file[1]/1024, 2)} KB)\n")
                                else:
                                    self.files_uploaded.insert("end", f"{file[0].replace(f'{file[2]} está subiendo el archivo ', '')} ({file[1]} B)\n")
                                
                                self.files_uploaded.yview("end")

                            self.files_uploaded.config(state="disabled")
                            
                except ConnectionAbortedError:
                    break
                except ConnectionResetError:
                    self.writeInChat(f"ERROR DE CONEXIÓN. INTENTA RECONECTAR.")
                    self.connected = False
            else:
                sleep(.2)

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