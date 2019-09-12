# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import os
import re
from urllib.parse import urlunsplit

def _convert_name_to_ev(name):
    return name.upper().replace('-', '_')

def _find_env_var(pattern):
   for ev in os.environ:
       if re.match(pattern, ev):
           return os.environ[ev]

def get_sws_service(instance_name):
    ievn = _convert_name_to_ev(instance_name)
    host = os.environ.get(ievn + '_SWS_SERVICE_HOST')
    port = os.environ.get(ievn + '_SWS_SERVICE_PORT')
    if host and port:
        return urlunsplit(('https', host, port, None, None))


