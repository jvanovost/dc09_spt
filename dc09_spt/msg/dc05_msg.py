# ----------------------------
# Class to implement the SIA DC05 message
# (c 2018 van Ovost Automatisering b.v.
# Author : Jacq. van Ovost
# ----------------------------
from dc09_spt.param import *
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


class dc05_codes:
    """
    Some special codes
    """
    @staticmethod
    def dc05_is_user(code):
        """
        Codes that have the user number following the code.
        Note that there is no way to transfer a zone in the message
        """
        codes_with_user = {"121",  "313",  "400",  "401",  "402",  "403",  "404",  "405",
                           "406",  "407",  "408",  "409",  "441",  "442",  "450",  "451",  "452",  "453",
                           "454",  "455",  "456",  "457",  "458",  "459",  "462",  "463",  "464",  "466",
                           "411",  "412",  "413",  "414",  "415",  "421",  "422",  "424",  "425",  "429",
                           "430",  "431",  "574",  "604",  "607",  "625",  "642",  "652",  "653"}
        return code in codes_with_user


class dc05_msg:
    @staticmethod
    def dc05event(spt_account,  params={}):   
        """
        Construct a DC05 message, also called Ademco Contact ID
        Parameters
            spt_account
                the account of the alarm transceiver.
                in most situations this will be used in the alarm message too, but for situations like
                a cloud based receiver, the account in the map will be different.
            params
                a map with key-value pairs.
                at this moment only the more commonly used fields are used.
                the currently handled keys are:
                    account
                        the account number.
                        most receivers expect 4 to 8 numeric digits
                    area
                        the area number in which the event happened
                        (area is a part of an installation that can arm and disarm independently)
                    zone
                        the alarm zone.
                    code
                        the event code in 3 numbers according to the DC05 standard.
                    q
                        the qualifier defining the state of the alarm.
                        1 means new alarm
                        3 means new restore
                        6 means old alarm
        """
        account = param.strpar(params,  'account',  spt_account)
        zone = param.numpar(params, 'zone',  '000')
        user = param.numpar(params, 'user',  None)
        msg = ''
        if account is None:
            msg += '#0000|'
        else:
            msg += '#' + account + '|'
        code = param.numpar(params,  'code',  '602')
        if len(code) != 3:
            raise Exception('Code should be 3 positions')
        q = param.numpar(params,  'q', '1')
        if q != '1' and q != '3' and q != '3':
            raise Exception('Qualifier q should be 1 or 3 or 6')
        area = param.numpar(params,  'area', '00')
        if len(area) != 2:
            area = ('00' + area)[-2:]
        if dc05_codes.dc05_is_user(code) and user is not None:
            if len(user) != 3:
                user = ('000' + user)[-3:]
            msg += q + code + ' ' + area + ' ' + user + ']'
        else:
            if len(zone) != 3:
                zone = ('000' + zone)[-3:]
            msg += q + code + ' ' + area + ' ' + zone + ']'
        return msg 
