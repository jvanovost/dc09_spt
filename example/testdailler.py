# ----------------------------
# Test dialler to show use of dc09_msg class
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
import sys
sys.path.append('../')
from dc09_spt import dc09_spt

import logging
logging.basicConfig(format='%(module)-12s %(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger()
#handler = logging.StreamHandler()
#logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

"""
    Copyright (c) 2018  van Ovost Automatisering b.v.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    you may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""

def callback(type, data):
    print("Callback type " + type + " data :")
    print(data)

key1 = b"\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12"
prom1 = "0123"
spt1 = dc09_spt.dc09_spt(prom1)
spt1.set_callback(callback)
spt1.set_path('main', 'primary', "welsum.ovost.nl", 12132, account=prom1, key = key1, type = 'UDP')
spt1.set_path('main', 'secondary', "ovost.eu", 12132,  account=prom1, key=key1, type = 'UDP')
spt1.start_poll(890, ok_msg={'code':  'YK'},  fail_msg={'code':  'YS'})
spt1.send_msg('SIA-DCS', {'code':'RR','text': 'Start of dialler'})
spt1.start_routine([{'start':  10.10,  'interval':  7200,  'time':  'now', 'type': 'SIA-DCS',  'code':  'RP'},
    {'interval':  3600,  'type': 'SIA-DCS',  'code':  'RP',  'zone':  99,  'time':  'now'}])

key2 = b"\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34\x56\x78\x90\x12\x34"
prom2="1234"
spt2 = dc09_spt.dc09_spt(prom2)
spt2.set_path('main', 'primary',"welsum.ovost.nl", 12128,  account=prom2, key=key2, type = 'UDP')
spt2.set_path('main', 'secondary', "ovost.eu", 12128,  account=prom2, key=key2, type = 'UDP')
spt2.set_path('back-up', 'primary',"ovost.eu", 12129,  account=prom2, key=key2)
spt2.set_path('back-up', 'secondary', "welsum.ovost.nl", 12129,  account=prom2, key=key2)
spt2.start_poll(85, 890,  ok_msg={'code':  '350'},  fail_msg={'code':  '350'})
spt2.send_msg('SIA-DCS', {'code':'RR','text': 'Start of dialler'})
spt2.send_msg('ADM-CID', {'account':  '124',  'code': 503, 'q': 1})

action = '0'

while action != '9':
    if spt1.isConnected():
        print('SPT1 connected')
    if spt2.isConnected():
        print('SPT2 connected')
    print(spt1.state())
    print(spt2.state())
    print ("What do we do ?\n 1 = open,\n 2 = close,\n 3 = burglary alarm,\n 4 = burglary restore,\n 5 = burglary trouble,\n 6 = trouble restore,\n 7 = start poll,\n 8 = stop poll,\n 9 = stop")
    action = input("action : ")
    print(action)
    if action == '1':
        spt1.send_msg('SIA-DCS', {'area': 2, 'areaname':  'Boven etage hoofdgebouw', 'code':'OP','user': 14,  'username': 'Jantje de Groot',  'text': 'Sectie uitgeschakeld',  'time':  'now'})
        spt2.send_msg('SIA-DCS', {'code':'OP','zone': 14,  'time':  'now'})
        spt2.send_msg('ADM-CID', {'account':  '124',  'code': 400, 'q': 1, 'zone': 14})
    if action == '2':
        spt1.send_msg('SIA-DCS', {'area': 2, 'areaname':  'Boven etage hoofdgebouw', 'code':'CL','user': 14,  'username': 'Jantje de Groot',  'text': 'Sectie ingeschakeld'})
        spt2.send_msg('SIA-DCS', {'code':'CL','zone': 14})
        spt2.send_msg('ADM-CID', {'account':  '124',  'code': 400, 'q': 3, 'zone': 14})
    if action == '3':
        spt1.send_msg('SIA-DCS', {'area': 2, 'time':  'now', 'areaname':  'Boven etage hoofdgebouw', 'code':'BA','zone': 3,  'zonename': 'Entree',  'text': 'Inbraakmelding magneetcontact'})
        spt2.send_msg('SIA-DCS', {'code':'BA','zone': 3, 'area': 2})
    if action == '4':
        spt1.send_msg('SIA-DCS', {'area': 2, 'time':  'now', 'areaname':  'Boven etage hoofdgebouw', 'code':'BR','zone': 3,  'zonename': 'Entree',  'text': 'Herstelmelding'})
        spt2.send_msg('SIA-DCS', {'code':'BR','zone': 3, 'area': 2})
    if action == '5':
        spt1.send_msg('SIA-DCS', {'area': 2, 'time':  'now', 'areaname':  'Boven etage hoofdgebouw', 'code':'BT','zone': 3,  'zonename': 'Entree',  'text': 'Sabotage magneetcontact'})
        spt2.send_msg('SIA-DCS', {'code':'BT','zone': 3, 'area': 2})
    if action == '6':
        spt1.send_msg('SIA-DCS', {'area': 2, 'time':  'now', 'areaname':  'Boven etage hoofdgebouw', 'code':'BJ','zone': 3,  'zonename': 'Entree',  'text': 'Sabotage Herstel'})
        spt2.send_msg('SIA-DCS', {'code':'BJ','zone': 3, 'area': 2})
    if action == '7':
        spt1.start_poll(85, 890)
        spt2.start_poll(850)
    if action == '9' or action == '8':
        spt1.stop_poll()
        spt2.stop_poll()
