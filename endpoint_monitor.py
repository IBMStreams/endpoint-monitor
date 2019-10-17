# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import collections
import time
import os
import streamsx.rest as sxr
import streamsx.rest_primitives as srp

Server = collections.namedtuple('Server', ['proto', 'ip', 'port', 'pe_id'])

def _get_server_address(op, pe):
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
        return Server(proto, ip, port, pe.id)

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
    ops_in_pe = {}
    servers = set()
    for op in job.get_operators():
        if op.operatorKind.startswith('com.ibm.streamsx.inet.rest::'):
            ops[op.name] = {'kind':op.operatorKind}
            pe = op.get_pe()
            server = _get_server_address(op, pe)
            if server:
                servers.add(server)
            pes[pe.id] = pe.launchCount
            # Map the operator to the pe that contains it
            if pe.id in ops_in_pe:
                ops_in_pe[pe.id].append(op.name)
            else:
                ops_in_pe[pe.id] = [op.name]

    return EndpointJob(name, generationId, applicationName, servers, ops, pes, ops_in_pe)


def _check_if_server_in_pe(job_info, pe_id):
    servers = [server for server in job_info.servers if server.pe_id == pe_id]
    if servers:
        return True
    return False

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
                    # Same job, same rest operators, same PEs

                    if not job_info.ops:
                        # no rest operators, thus we don't care about it
                        jobs[j.id] = job_info
                        continue

                    # has rest operators, for each pe, check if pe launchCounts are the same
                    # if same -> Get all ops in that PE, check if any of those ops have an existing server (assumes if more than 1 rest op in PE, they all share 1 server object), if not PE is just starting up
                    # if not  -> Check if PE's server is back up
                    #   if yes, add it and update PE launchCount, then remove old invalid servers
                    #   if no, don't do anything (need to wait for server to come back up)
                    servers_to_add = set()
                    pes = job_info.pes
                    pes_changed = []

                    for pe in j.get_pes():
                        # Get the names of all the rest operators in this PE, use get bc some pes might not have any rest operators
                        op_names = job_info.ops_in_pe.get(pe.id)
                        if op_names is None:
                            # PE does not contain any rest operators, thus don't care about it, go onto next PE
                            continue
                        if pes[pe.id] == pe.launchCount:
                            print("SAME LAUNCHCOUNT")
                            # Check if this PE has any existing servers
                            if not _check_if_server_in_pe(job_info, pe.id):
                                # PE launchCount same, and no servers in this PE, thus server just starting up, check if it is up and running
                                for op_name in op_names:
                                    op_obj = j.get_operators(op_name)
                                    if op_obj: # TODO Do i need this if check?
                                        new_server = _get_server_address(op_obj[0], pe)
                                        if new_server:
                                            # New server is up and running, add it, assumes 1 server/PE (even if more than 1 rest operator in a PE)
                                            servers_to_add.add(new_server)
                                            break
                        else:
                            print("DIFFERENT LAUNCHCOUNT")
                            # PE launchCount different, thus PE restarted, iterate through the op names in this PE
                            # For each op name, get the actual op object and check if new server is up
                            for op_name in op_names:
                                op_obj = j.get_operators(op_name)
                                if op_obj: # TODO Do i need this if check?
                                    new_server = _get_server_address(op_obj[0], pe)
                                    if new_server:
                                        # New server is up and running, add it, assumes 1 server/PE (even if more than 1 rest operator in a PE), update PE launchCount
                                        servers_to_add.add(new_server)
                                        pes[pe.id] = pe.launchCount
                                        # Add the PE to the list, so we can find & remove all the old invalid servers that have this pe id
                                        pes_changed.add(pe.id)
                                        break

                    # After checking all PE's, if any new servers, remove old invalid ones and update job's servers
                    if servers_to_add:
                        # Remove the old servers where the PE's launchCounts have changed
                        servers_to_remove = set([x for x in job_info.servers if x.pe_id in pes_changed])
                        valid_servers = job_info.servers - servers_to_remove
                        # Add the new servers
                        new_servers = valid_servers.union(servers_to_add)
                        # Update the job w/ the new info
                        jobs[j.id] = EndpointJob(job_info.name, job_info.generationId, job_info.applicationName, new_servers, job_info.ops, pes, job_info.ops_in_pe)
                    else:
                        # PE's may or may not have restarted, but no new servers are up, thus don't update job, don't change config
                        jobs[j.id] = job_info
                    print(jobs[j.id])
                    continue
            print("CREATING NEW JOB")
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

class EndpointJob:
    def __init__(self, name, generationId, applicationName, servers=set(), ops={}, pes={}, ops_in_pe={}):
        self.name = name
        self.generationId = generationId
        self.applicationName = applicationName
        self.servers = servers
        self.ops = ops # Dictionary mapping rest operator name's to operatorKind
        self.pes = pes # Dictionary mapping PE id's to their launchCount
        self.ops_in_pe = ops_in_pe # Dictionary mapping a PE.id to a list of the names of rest operators, that given PE contains (ie ops_in_pe[pe_id] = [op1_name, op2_name])

    def __str__(self):
        return "servers=%s, ops=%s, pes=%s" % (self.servers, self.ops, self.pes)