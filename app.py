import os
import re
import subprocess
import streamsx.scripts.info as info

from file_config import FileWriter
from endpoint_monitor import EndpointMonitor
import streams_openshift

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
    sig_file = os.path.join(SECRETS, 'streams-auth', 'signature.secret')
    return os.path.exists(sig_file)

info.main()

# Name of the IbmStreamsInstance object
instance_name = os.environ['STREAMSX_ENDPOINT_INSTANCE']
sws_service = streams_openshift.get_sws_service(instance_name)

if not sws_service:
    raise ValueError("Cannot find Streams SWS service for instance {0}".format(instance_name))
    
print("IBMStreamsInstance:", instance_name)
print("SWS Service:", sws_service)

job_group_pattern = os.environ['STREAMSX_ENDPOINT_JOB_GROUP']
#job_filter = lambda job : re.match(job_group_pattern, job.jobGroup)
job_filter = lambda job : job.jobGroup.endswith('/'+job_group_pattern)
print("Job group pattern:", job_group_pattern)

client_cert = _process_streams_certs()

cfg = FileWriter(location=os.path.join(OPT, 'job-configs'), client_cert=client_cert, signature=_has_signature_secret())

em = EndpointMonitor(endpoint=sws_service, config=cfg, job_filter=job_filter, verify=False)
em.run()
