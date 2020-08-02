# ----------------------------
# Transmit class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import socket
import logging


class TransPathTCP:
    def __init__(self, host, port,  timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.s = None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(self.timeout)
            self.s.connect((self.host, self.port))
        except Exception as e:
            self.s = None
            logging.error('TCP Connect to host %s port %s exception %s',  self.host,  self.port,  e)
        return self.s
        
    def send(self, msg):
        if self.s is not None:
            try:
                self.s.send(msg)
            except Exception as e:
                self.s = None
                logging.error('TCP send message to host %s port %s exception %s',  self.host, self.port, e)
    
    def receive(self, length=1024):
        antw = None
        if self.s is not None:
            try:
                antw = self.s.recv(length)
            except Exception as e:
                self.s = None
                logging.error('TCP receive message from host %s port %s exception %s',  self.host, self.port, e)
        return antw

    def sendAndReceive(self, msg, max_answ=1024):
        antw = None
        if self.s is not None:
            try:
                self.s.send(msg)
            except Exception as e:
                self.s = None
                logging.error('TCP send message to host %s port %s exception %s',  self.host, self.port, e)
            try:
                antw = self.s.recv(max_answ)
            except Exception as e:
                self.s = None
                logging.error('TCP receive message from host %s port %s exception %s',  self.host, self.port, e)
        return antw

    def disconnect(self):
        if self.s is not None:
            self.s.close()
            self.s = None
