# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import os
import re

def _convert_name_to_ev(name):
    return name.upper().replace('-', '_')

def _find_env_var(pattern):
   for ev in os.environ:
       if re.match(pattern, ev):
           return os.environ[ev]

def get_sws_service(instance_name):
    ievn = _convert_name_to_ev(instance_name)
    host = _find_env_var(ievn + '_REST_SERVICE_HOST')
    port = _find_env_var(ievn + '_REST_SERVICE_PORT')
    if host and port:
        return 'https://{0}:{1}'.format(host, port)


