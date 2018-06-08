# ----------------------------
# Transmit class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import socket
import logging

class TransPathUDP:
    def __init__(self, host, port,  timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.s = None

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.settimeout(self.timeout)
        except Exception as e:
            s = None
            logging.error('UDP Socket creation exception %s',  e)
        return s
        
    def send(self, msg):
        if self.s != None:
            try:
                cmsg = str.encode(msg)
                self.s.sendto(cmsg, (self.host, self.port))
            except Exception as e:
                self.s = None
                logging.error('UDP send message to host %s port %s exception %s',  self.host,  self.port,  e)
    
    def receive(self, length=1024):
        if self.s != None:
            try:
                antw=self.s.recvfrom(length)
            except Exception as e:
                self.s = None
                logging.error('UDP receive message from host %s port %s exception %s',  self.host,  self.port,  e)
        return antw

    def disconnect(self):
        if self.s != None:
            self.s.close()
            self.s=None

