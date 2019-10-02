# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import collections
import time
import os
import streamsx.rest as sxr
import streamsx.rest_primitives

Server = collections.namedtuple('Server', ['proto', 'ip', 'port', 'oid'])

def _get_server_address(op):
    pe = op.get_pe()
    # No get_resource on PE
    pe_resource = streamsx.rest_primitives.Resource(pe.rest_client.make_request(pe.resource), pe.rest_client)
    ip = pe_resource.ipAddress
    port = None
    https = None
    for m in op.get_metrics():
        if m.name == 'serverPort':
            port = m.value
        elif m.name == 'https':
            https = m.value
    
    if ip and port:
        proto = 'https' if https else 'http'
        return Server(proto, ip, port, op.name)


def _job_new_incarnation(job):
    """Obtain the full server information for a job
    for a new job or modified job (change of generation id)

    Returns an object with all the required job information
    and REST endpoints (if any)
    """
    job_info = {'servers':set(), 'ops':dict(), 'pes':dict()}
    for k in ['name', 'generationId', 'applicationName']:
        job_info[k] = getattr(job, k)
    for op in job.get_operators():
        if op.operatorKind.startswith('com.ibm.streamsx.inet.rest::'):
            job_info['ops'][op.name] = {'kind':op.operatorKind}
            server = _get_server_address(op)
            if server:
                job_info['servers'].add(server)
    return job_info

class EndpointMonitor(object):
    def __init__(self, endpoint, config, job_filter, verify=None):
        self._jobs = {}
        self._url = endpoint + '/streams/rest/resources'
        self._config = config
        self._job_filter = job_filter
        self._verify = verify
        self._sc = None

    @property
    def instance(self):
        if self._sc is None:
            self._sc = sxr.StreamsConnection(os.environ['STREAMS_USERNAME'], os.environ['STREAMS_PASSWORD'], resource_url=self._url)
            if self._verify is not None:
                self._sc.session.verify = self._verify
            self._ins = self._sc.get_instances()[0]
        return self._ins

    def _survey_jobs(self):
        """ Detect all jobs with REST operators.
        """
        jobs = {}
        for j in self.instance.get_jobs():
            if not self._job_filter(j):
                continue
            if 'running' != j.status:
                continue

            job_info = self._jobs.get(j.id)
            # Check for existing job
            if job_info:
                if j.generationId == job_info['generationId']:
                    # No rest operators, no change in job
                    if not job_info['servers']:
                        continue

                    # TODO update operator info only
                    pass

            jobs[j.id] = _job_new_incarnation(j)

        return jobs

    def _update(self):
        print("Scan for jobs")
        current_jobs = self._survey_jobs()
        existing_jobs = list(self._jobs.keys())
        print("Existing jobs", existing_jobs)
        for jobid in existing_jobs:
            ne = current_jobs.pop(jobid, None)
            if ne is None:
                self._delete_job(jobid)
            elif ne['servers'] != self._jobs[jobid]['servers']:
                self._update_job(jobid, ne)
        for jobid in current_jobs:
            self._new_job(jobid, current_jobs[jobid])

    def _delete_job(self, jobid):
        print("DELETE:", jobid, self._jobs[jobid])
        if self._jobs[jobid]['servers']:
            self._config.delete(jobid, self._jobs[jobid])
        del self._jobs[jobid]

    def _update_job(self, jobid, ne):
        print("UPDATE:", jobid, ne)
        if ne['servers']:
            self._config.update(jobid, self._jobs[jobid], ne)
        self._jobs[jobid] = ne

    def _new_job(self, jobid, ne):
        print("NEW:", jobid, ne, bool(ne['servers']))
        if ne['servers']:
            self._config.create(jobid, ne)
        self._jobs[jobid] = ne

    def run(self):
        self._config.clean()
        while True:
            try:
                 self._update()
                 time.sleep(5)
            except IOError as e:
                 self._sc = None
                 print("ERROR", e)
                 time.sleep(1)

