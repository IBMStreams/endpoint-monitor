# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import os

class FileWriter(object):
    def __init__(self, location, client_cert, signature):
        self._location = location
        self._signature = signature
        if not os.path.exists(self._location):
            os.mkdir(self._location)
        self._client_cert = client_cert
        self._pipe_name = os.path.join(location, 'actions')
        
    def _reload(self):
        print('Monitor', 'RELOAD!')
        with open(self._pipe_name, 'w') as f:
            f.write('reload\n')
        print('Monitor', 'RELOADED!')

    def clean(self):
        # Remove all nginx-streams-job-%s.conf
        if not os.path.exists(self._pipe_name):
            os.mkfifo(self._pipe_name)
  
    def create(self, jobid, job_config):
        if job_config.name == job_config.applicationName + '_' + jobid:
            location = '/streams/jobs/' + str(jobid) + '/'
        else:
            location = '/' + job_config.name + '/'

        job_config.config_file = self._write_file(jobid, location, job_config)
        self._reload()

    def delete(self, jobid, job_config):
        if hasattr(job_config, 'config_file'):
            os.remove(job_config.config_file)
        self._reload()

    def update(self, jobid, old_job_config, job_config):
        # TEMP
        self.delete(jobid, old_job_config)
        self.create(jobid, job_config)

    def _write_file(self, jobid, location, job_config):
        cfn = 'nginx-streams-job-%s.conf' % jobid
        tfn = cfn + '.tmp'
        fcfn = os.path.join(self._location, cfn)
        ftfn = os.path.join(self._location, tfn)
        with open(ftfn, 'w') as f:
            self._config_contents(f, jobid, location, job_config)
        os.rename(ftfn, fcfn)
        return fcfn

    def _config_contents(self, f, jobid, location, job_config):
        # Work-around dojo not in v5 app images
        f.write('location ^~ %sstreamsx.inet.dojo/ {\n' % location)
        f.write('  proxy_pass https://ajax.googleapis.com/ajax/libs/dojo/1.14.1/;\n')
        f.write('}\n')

        multi_servers = len(job_config.servers) > 1

        for server in job_config.servers:
            proto = server.proto
            details = job_config.server_details[server]
            server_root_url = details.url
 
            # The job is exposed as a single logical entry
            # under location/*

            # However the job may contain multiple REST endpoint
            # operators in multiple servers. This is to avoid forcing
            # unrelated operators into the same PE and hence same
            # server. For example an inject operator should not be
            # forced into a tuple view (expose) operator that
            # is at the end of the analytic flow.

            # This for example we may have operators of:
            # C1/A  - Server S1
            # C2/B  - Server S1
            # C1/C  - Server S2
            
            # Thus we create proxy mappings as follows:

            # Contexts that will resolve static files
            # exposed by the operator(s)
            # The assumption is that if a job is exposing a context
            # and resource files then they files are consistent across
            # operators.
            # C1    ----> S1/C1
            # C2    ----> S1/C2
            # C1    ----> S2/C1

            # Operator paths that will resolve paths specific
            # to an individual operator's ports/streams
            # C1/A  ----> S1/C1/A
            # C2/B  ----> S1/C2/B
            # C1/C  ----> S2/C1/C
       
            if multi_servers:
                for p in details.paths:
                    loc = location + p + '/'
                    url = server_root_url + p + '/'
                    self._proxy_entry(f, loc, proto, url)

                for c in details.contexts:
                    loc = location + c + '/'
                    url = server_root_url + c + '/'
                    self._proxy_entry(f, loc, proto, url)

            # Aliases to operator functional paths (e.g. inject)
            for a,p in details.aliases.items():
                loc = location + a 
                url = server_root_url + p
                self._proxy_entry(f, loc, proto, url)

        # A final catch all
        # Is the sole location for a single server
        # Maps to only one of the servers.
        self._proxy_entry(f, location, proto, server_root_url)

    def _proxy_entry(self, f, location, proto, target_url):

        # If we are checking signatures then two locations are
        # created. The external one that invokes Javascript
        # to verify the signature and then redirect to the internal one.
        # The internal is the full proxy one but is only visible within
        # the server (as it is not protected by any signature authentication).

        # The external location
        f.write('location ^~ %s {\n' % location)
        if self._signature:
            f.write("  set $redirectLocation '/@internal%s';\n" % location)
            f.write("  js_content checkHTTP;\n")
        else:
            self._proxy_location(f, proto, target_url)
        f.write('}\n')

        if self._signature:
            f.write('location ~^ /@internal%s {\n' % location)
            f.write('  internal;\n');
            self._proxy_location(f, proto, target_url)
            f.write('}\n')

    def _proxy_location(self, f, proto, url):

        f.write('  proxy_set_header Host $host;\n')
        f.write('  proxy_set_header X-Real-IP $remote_addr;\n')
        f.write('  proxy_set_header X-Forwarded-Proto %s ;\n' % proto)
        f.write('  proxy_set_header  X-Forwarded-For $remote_addr;\n')
        f.write('  proxy_set_header  X-Forwarded-Host $remote_addr;\n')
        f.write('  proxy_pass %s;\n' % url)

        if proto == 'https':
            if self._client_cert:
                f.write('  proxy_ssl_certificate %s;\n' % self._client_cert[0])
                f.write('  proxy_ssl_certificate_key %s;\n' % self._client_cert[1])
