import os
import re
import streamsx.scripts.info as info

from file_config import FileWriter
from endpoint_monitor import EndpointMonitor
import streams_openshift

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

cfg = FileWriter(location='/opt/streams_job_configs')

em = EndpointMonitor(endpoint=sws_service, config=cfg, job_filter=job_filter, verify=False)
em.run()



