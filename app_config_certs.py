# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import os
import base64

# Create a Streams application configuration 
# from the -certs secret that can be used by the rest operators.

def create_app_config(inst, name, location):
    ac = _get_contents(location)
    for existing in inst.get_application_configurations(name=name):
        if existing.name == name:
            if existing.properties == ac:
                return
            existing.update(properties=ac)
            return
        
    inst.create_application_configuration(name, ac, 'Endpoint-monitor created Jetty server certificates')

def _get_contents(location):

    ac = {}

    _add_text_file(ac, 'server.pass', location)

    _add_binary_file(ac, 'server.jks', location)
    _add_binary_file(ac, 'cacerts.jks', location)

    return ac

def _add_text_file(ac, key, location):
    with open(os.path.join(location, key), 'r') as f:
        ac[key] = f.read()

def _add_binary_file(ac, key, location):
    with open(os.path.join(location, key), 'rb') as f:
        value = f.read()

    ac[key] = base64.b64encode(value).decode('ascii')

