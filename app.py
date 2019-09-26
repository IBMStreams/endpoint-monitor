import os
import re
import subprocess
import streamsx.scripts.info as info

from file_config import FileWriter
from endpoint_monitor import EndpointMonitor
import streams_openshift

OPT = '/var/opt/streams-endpoint-monitor'
SECRETS = '/var/run/secrets/streams-endpoint-monitor'

def _unpack_restop_certs():
    cert_file = os.path.join(SECRETS, 'streams-certs', 'client.pfx')
    if not os.path.exists(cert_file):
        return

    pwd_file = os.path.join(SECRETS, 'streams-certs', 'client.pass')
    certs_dir = os.path.join(OPT, 'streams-certs')
    if not os.path.exists(certs_dir):
        os.mkdir(certs_dir)
    crt = os.path.join(certs_dir, 'client.crt')
    rsa = os.path.join(certs_dir, 'client.rsa')

    ossl = '/usr/bin/openssl'
    args = ['/usr/bin/openssl', 'pkcs12', '-in', cert_file, '--pass', 'file:' + pwd_file]
    subprocess.run(args + ['-clcerts', '-nokeys', '-out', crt], check=True)
    subprocess.run(args + ['-nocerts', '-nodes', '-out', rsa], check=True)
    return crt, rsa

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

client_cert = _unpack_restop_certs()

cfg = FileWriter(location=os.path.join(OPT, 'job-configs'), client_cert=client_cert)

em = EndpointMonitor(endpoint=sws_service, config=cfg, job_filter=job_filter, verify=False)
em.run()
