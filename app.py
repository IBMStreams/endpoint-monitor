# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import logging
import os
import re
import time
import subprocess
import streamsx.scripts.info as info

from file_config import FileWriter
from multi_config import MultiConfig
from swagger_config import SwaggerConfig
from endpoint_monitor import EndpointMonitor
import app_config_certs
import streams_openshift

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

LOGGER = logging.getLogger('streamsx.endpoint_monitor.app')

OPT = '/var/opt/streams-endpoint-monitor'
SECRETS = '/var/run/secrets/streams-endpoint-monitor'

def _convert_client_cert():
    """
      Convert the client certificate pfx to crt/rsa required by nginx.
      If the certificate does not exist then no action is taken.
    """
    cert_file = os.path.join(SECRETS, 'streams-certs', 'client.pfx')
    if not os.path.exists(cert_file):
        return

    pwd_file = os.path.join(SECRETS, 'streams-certs', 'client.pass')
    certs_dir = os.path.join(OPT, 'streams-certs')
    if not os.path.exists(certs_dir):
        os.mkdir(certs_dir)
    crt = os.path.join(certs_dir, 'client.crt')
    rsa = os.path.join(certs_dir, 'client.rsa')

    args = ['/usr/bin/openssl', 'pkcs12', '-in', cert_file, '-password', 'file:' + pwd_file]
    subprocess.run(args + ['-clcerts', '-nokeys', '-out', crt], check=True)
    subprocess.run(args + ['-nocerts', '-nodes', '-out', rsa], check=True)
    return crt, rsa

def _process_streams_certs():
    """
    Take the certificate information from the streams-certs to:
        * convert the client certificate pfx to crt/rsa required by nginx
    """
    client_cert = _convert_client_cert()

    return client_cert

def _has_signature_secret():
    sig_file = os.path.join(SECRETS, 'server-auth', 'signature-secret')
    LOGGER.info('Signature secret file: %s exists %s', sig_file, os.path.exists(sig_file))
    return os.path.exists(sig_file)

info.main()

# Name of the IbmStreamsInstance object
instance_name = os.environ['STREAMSX_ENDPOINT_INSTANCE']
sws_service = streams_openshift.get_sws_service(instance_name)

if not sws_service:
    raise ValueError("Cannot find Streams SWS service for instance {0}".format(instance_name))
    
LOGGER.info("IBMStreamsInstance: %s", instance_name)
LOGGER.info("SWS Service: %s", sws_service)

job_group_pattern = os.environ['STREAMSX_ENDPOINT_JOB_GROUP']
#job_filter = lambda job : re.match(job_group_pattern, job.jobGroup)
job_filter = lambda job : job.jobGroup.endswith('/'+job_group_pattern)
LOGGER.info("Job group pattern: %s", job_group_pattern)

client_cert = _process_streams_certs()

cfg = FileWriter(location=os.path.join(OPT, 'job-configs'), client_cert=client_cert, signature=_has_signature_secret())

swagger = SwaggerConfig(os.path.join(OPT, 'swagger-defs'), instance_name)

cfg = MultiConfig(cfg, swagger)

em = EndpointMonitor(endpoint=sws_service, config=cfg, job_filter=job_filter, client_cert=client_cert, verify=False)

# Create the application configuration
certs_secret = os.path.join(SECRETS, 'streams-certs')
server_pass = os.path.join(certs_secret, 'server.pass')
if os.path.exists(server_pass):
    LOGGER.info("HTTPS endpoints supported:")
    app_cfg_name = os.environ['STREAMSX_ENDPOINT_NAME'] + '-streams-certs'
    app_config_certs.create_app_config(em.instance, app_cfg_name, certs_secret)
    LOGGER.info("Created Streams application configuration for endpoints: %s", app_cfg_name)


active_file = os.path.join(OPT, 'monitor.active')
with open(active_file, 'w') as f:
    f.write(time.asctime())
    f.write("\n")

try:
    em.run()
finally:
    os.remove(active_file)
