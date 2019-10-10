# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import collections
import time
import os
import streamsx.rest as sxr
import streamsx.rest_primitives as srp

Server = collections.namedtuple('Server', ['proto', 'ip', 'port', 'oid'])

def _get_server_address(op):
    pe = op.get_pe()
    # No get_resource on PE
    pe_resource = srp.Resource(pe.rest_client.make_request(pe.resource), pe.rest_client)
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
        return pe, Server(proto, ip, port, op.name)


def _job_new_incarnation(job):
    """Obtain the full server information for a job
    for a new job or modified job (change of generation id)

    Returns an object with all the required job information
    and REST endpoints (if any)
    """
    name = getattr(job, 'name')
    generationId = getattr(job, 'generationId')
    applicationName = getattr(job, 'applicationName')
    ops = {}
    pes = {}
    servers = set()
    for op in job.get_operators():
        if op.operatorKind.startswith('com.ibm.streamsx.inet.rest::'):
            ops[op.name] = {'kind':op.operatorKind}
            pe, server = _get_server_address(op)
            if server:
                servers.add(server)
                pes[pe.id] = pe.launchCount

    return _Localjob(name, generationId, applicationName, servers, ops, pes)

class EndpointMonitor(object):
    def __init__(self, endpoint, config, job_filter, verify=None):
        self._jobs = {}
        self._endpoint = endpoint
        self._config = config
        self._job_filter = job_filter
        self._verify = verify
        self._inst = None

    @property
    def instance(self):
        if self._inst is None:
            self._inst = srp.Instance.of_endpoint(endpoint=self._endpoint, verify=self._verify)
        return self._inst

    def _survey_jobs(self):
        """ Detect and return all jobs with REST operators.
        """
        jobs = {}
        for j in self.instance.get_jobs():
            # Check if job j is one of the jobs we want to look at
            if not self._job_filter(j):
                continue
            # Check if job j is running, if not, maybe its either spinning up or winding down?
            if 'running' != j.status:
                continue

            job_info = self._jobs.get(j.id)
            # Check for existing job
            if job_info:
                # Check if hash of existing job j is the same as before
                if j.generationId == job_info.generationId:

                    if not job_info.ops:
                        # Same job, no rest operators, thus we don't care about it
                        # No rest operators, no change in job
                        jobs[j.id] = job_info
                        continue

                    # TODO update operator info only
                    pass
            # New job, or job has changed (new generationId) - maybe now has a rest operator?
            jobs[j.id] = _job_new_incarnation(j)

        return jobs

    def _update(self):
        print("Scan for jobs")
        current_jobs = self._survey_jobs()
        existing_jobs = list(self._jobs.keys())
        print("Existing jobs", existing_jobs)
        for jobid in existing_jobs:
            # Check if existing job is still running
            ne = current_jobs.pop(jobid, None)
            if ne is None:
                self._delete_job(jobid)
            # Job still running
            # Check if job's servers have changed, if so update nginx config
            elif ne.servers != self._jobs[jobid].servers:
                self._update_job(jobid, ne)
        for jobid in current_jobs:
            self._new_job(jobid, current_jobs[jobid])

    def _delete_job(self, jobid):
        print("DELETE:", jobid, self._jobs[jobid])
        if self._jobs[jobid].servers:
            self._config.delete(jobid, self._jobs[jobid])
        del self._jobs[jobid]

    def _update_job(self, jobid, ne):
        print("UPDATE:", jobid, ne)
        if ne.servers:
            self._config.update(jobid, self._jobs[jobid], ne)
        self._jobs[jobid] = ne

    # ne is the jobid's job_info
    def _new_job(self, jobid, ne):
        print("NEW:", jobid, ne, bool(ne.servers))
        if ne.servers:
            self._config.create(jobid, ne)
        self._jobs[jobid] = ne


    def run(self):
        self._config.clean()
        while True:
            try:
                 self._update()
                 time.sleep(5)
            except IOError as e:
                 self._inst = None
                 print("ERROR", e)
                 time.sleep(1)

class _Localjob:
    def __init__(self, name, generationId, applicationName, servers=set(), ops={}, pes={}):
        self.name = name
        self.generationId = generationId
        self.applicationName = applicationName
        self.servers = servers
        self.ops = ops
        self.pes = pes

    def __str__(self):
        return "servers=%s, ops=%s, pes=%s" % (self.servers, self.ops, self.pes)