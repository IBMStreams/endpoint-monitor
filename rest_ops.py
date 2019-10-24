# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

#
# Code that handles specifics and interactions
# with the Jetty servers running in the REST operators.
#

import requests
import endpoint_monitor

def server_url(server):
    return '%s://%s:%s/' % (server.proto, server.ip, server.port)

# Pull information ports/info for the Jetty server to
# identify contexts, paths and exposed ports.
#
# Returns set of contexts, set of paths and the exposed ports information

def _find_contexts(server, url, client_cert):
    oppaths=set()
    contexts=set()
    exposed_ports = None
    ports_url = url + 'ports/info'
    ports = requests.get(ports_url, cert=client_cert, verify=False).json()
    if 'exposedPorts' in ports:
        exposed_ports = ports['exposedPorts']
        for port in exposed_ports:
            cps = port['contextPaths']
            for id_ in cps:
                cp = cps[id_].replace('\\', '')
                scp = cp.split('/')
                contexts.add(scp[1])
                oppaths.add(scp[1]+'/'+scp[2])

    return contexts, oppaths, exposed_ports

def _make_port_alias(path, port, output=True):
    r = '/ports/'
    r += 'output' if output else 'input'
    r += '/'
    r += str(port)
    r += '/'
    alias = path.replace(r)
    if alias != path:
        return path

def _add_alias(aliases, path, port, output=True):
    alias = _make_port_alias(inject, 0)
    if alias:
        aliases[alias] = inject

def _create_aliases(ports):
    aliases = {}
    for port in ports:
        kind = port['operatorKind']
        if kind == 'com.ibm.streamsx.inet.rest::HTTPJsonInject':
            cps = port['contextPaths']
            _add_alias(aliases, cps['inject'], 0)

    return aliases
    
#
# Fills in the details for a given server to return
# a ServerDetail tuple.
#
def fill_in_details(endjob, client_cert):
    for server in endjob.servers:
        url = server_url(server)
        contexts, paths, ports = _find_contexts(server, url, client_cert)
        aliases = _create_aliases(ports)
        print('Aliases', aliases)
        endjob.server_details[server] = endpoint_monitor.ServerDetail(url, contexts, paths, ports)
        print('Server', server)
        print('ServerDetail', endjob.server_details[server])
