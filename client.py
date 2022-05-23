from logging import error
import socket
import threading
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog

HOST = '25.61.192.46'
PORT = 5050
FORMAT = 'UTF-8'
HEADER = 1024
VERSION = "1.0.1"

class Client():
    def __init__(self, host, port):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.addr)

        msg = tkinter.Tk()
        msg.withdraw()

        self.nickname = simpledialog.askstring("Usuario", "Elige tu nombre de usuario", parent=msg)

        self.gui_done = False
        self.running = True

        gui_thread = threading.Thread(target=self.gui_loop)
        receive_thread = threading.Thread(target=self.receive)
        gui_thread.start()
        receive_thread.start()

    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title(f"NotDiscord v{VERSION}")
        self.win.configure(bg="lightgray")

        self.chat_label = tkinter.Label(self.win, text="Chat:", bg="lightgray")
        self.chat_label.config(font=("Arial", 12))
        self.chat_label.pack(padx=20, pady=5)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx=20, pady=5)
        self.text_area.config(state="disabled")

        self.msg_label = tkinter.Label(self.win, text="Message:", bg="lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)

        self.input_area = tkinter.Text(self.win, height=3)
        self.input_area.pack(padx=20, pady=5)

        self.send_button = tkinter.Button(self.win, text="Send", command=self.write)
        self.send_button.config(font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5)
        self.win.bind('<Return>', lambda event=None: self.send_button.invoke())

        self.gui_done = True
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def write(self):
        msg = f"{self.input_area.get('1.0', 'end')}"
        if len(msg.strip()) > 0:
            self.sock.send(msg.encode(FORMAT))
            self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        self.win.destroy()
        self.sock.close()
        exit(0)

    def receive(self):
        while self.running:
            try:
                msg = self.sock.recv(HEADER).decode(FORMAT)
                if msg == "NICK":
                    self.sock.send(self.nickname.encode(FORMAT))
                elif self.gui_done and len(msg.strip()) > 0:
                    self.text_area.config(state="normal")
                    self.text_area.insert("end", f"\n{msg}")
                    self.text_area.yview("end")
                    self.text_area.config(state="disabled")
            except ConnectionAbortedError:
                break
            except error as e:
                print(e)
                self.sock.close()
                break

client = Client(HOST, PORT)
