import os
import streamsx.scripts.info as info

from file_config import FileWriter
from endpoint_monitor import EndpointMonitor

info.main()

url = os.environ['STREAMS_ENDPOINT_INSTANCE_URL']

cfg = FileWriter(location='/opt/streams_job_configs')

em = EndpointMonitor(resource_url=url, config=cfg, job_filter=lambda job: True, verify=False)
em.run()



