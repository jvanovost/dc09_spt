
class param:
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
    # ------------------------------
    # Fetch a numeric parameter
    # and make sure it is a string
    # ------------------------------
    @staticmethod
    def numpar(map,  name,  default=None):
        res = map.get(name, default)
        if res is not None:
            if not isinstance(res, str):
                res = str(res)
            if not res.isdigit():
                raise Exception(name + ' is not numeric')
        return res

    @staticmethod
    def strpar(map,  name,  default=None):
        res = map.get(name, default)
        if res is not None:
            if not isinstance(res, str):
                res = str(res)
        return res
