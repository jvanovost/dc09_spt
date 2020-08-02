# ----------------------------
# Transmit class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import logging
from dc09_spt.comm.transpathtcp import TransPathTCP
from dc09_spt.comm.transpathudp import TransPathUDP


class TransPath:
    """
    Handle the basic tasks for establishing and maintaining a transmit path
    """
    def __init__(self,  host,  port,  account, *, key=None,  receiver=None,  line=None,  timeout=5.0,  type=None):
        self.host = host
        self.port = port
        self.offset = 0
        self.timeout = timeout
        self.receiver = receiver
        if type is not None:
            self.type = type.lower()
        else:
            self.type = 'tcp'
        self.account = account
        self.key = key
        self.line = line

    def set_offset(self, offset):
        self.offset = offset

    def get_offset(self):
        return self.offset
    
    def get_key(self):
        return self.key
    
    def get_receiver(self):
        return self.receiver

    def get_line(self):
        return self.line
        
    def get_account(self):
        return self.account

    def connect(self):
        if self.type == 'tcp':
            conn = TransPathTCP(self.host, self.port)
        elif self.type == 'udp':
            conn = TransPathUDP(self.host, self.port)
        else:
            conn = None
            logging.error('Undefined connection type : %s',  self.type)
        if conn is not None:
            conn.connect()
        return conn
        
    @staticmethod
    def disconnect(conn):
        if conn is not None:
            conn.disconnect()
