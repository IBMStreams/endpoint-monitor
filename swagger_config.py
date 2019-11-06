# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import json
import os

TEMPLATES = os.path.join(os.path.dirname(__file__), 'swagger')

class SwaggerConfig(object):
    def __init__(self, location, instance):
        self._location = location
        self._instance = instance
        if not os.path.exists(self._location):
            os.mkdir(self._location)
        self.clean()

    def _update_jobs_file(self):
        cfn = 'jobs.js'
        tfn = cfn + '.tmp'
        fcfn = os.path.join(self._location, cfn)
        ftfn = os.path.join(self._location, tfn)
        with open(ftfn, 'w') as f:
            f.write("job_urls = JSON.parse('")
            json.dump(list(self._jobs.values()), f)
            f.write("')")
        os.rename(ftfn, fcfn)

    def clean(self):
        self._jobs = {}
        self._update_jobs_file()
  
    def create(self, jobid, job_config):
        name, file = self._create_swagger_file(jobid, job_config)
        job_config.swagger_file = file
        self._jobs[jobid] = {'url':'swagger-defs/'+name+'.json', 'name':name}
        self._update_jobs_file()

    def delete(self, jobid, job_config):
        if hasattr(job_config, 'swagger_file'):
            os.remove(job_config.swagger_file)
            del self._jobs[jobid]
        self._update_jobs_file()

    def update(self, jobid, old_job_config, job_config):
        self.delete(jobid, old_job_config)
        self.create(jobid, job_config)

    def _create_swagger_file(self, jobid, job_config):
        name = job_config.alias
        fname = os.path.join(self._location, name + '.json')
        tname = os.path.join(self._location, fname + '.tmp')
        with open(tname, 'w') as f:
            swg = self._job_swagger(name, jobid, job_config)
            self._aliases_swagger(swg, job_config)
            json.dump(swg, f)
        os.rename(tname, fname)
        return name, fname

    def _job_swagger(self, name, jobid, job_config):
        with open(os.path.join(TEMPLATES, 'job.json')) as f:
            swg = json.load(f)

        desc = swg['info']['description']
        swg['info']['description'] = desc.format(
            job_id=jobid, job_name=job_config.name, instance_id=self._instance)
        title = swg['info']['title']
        swg['info']['title'] = title.format(job_name=name)
        swg['basePath'] = job_config.path

        contexts = set()
        for server in job_config.servers:
            details = job_config.server_details[server]
            contexts.update(details.contexts)
        tags = swg['tags']
        for ctx in contexts:
            tags.append({'name':ctx})
   
        return swg

    def _aliases_swagger(self, swg, job_config):
        for server in job_config.servers:
            paths = swg['paths']
            details = job_config.server_details[server]
            for alias, info in details.aliases.items():
                kind = info['kind']
                if kind == 'com.ibm.streamsx.inet.rest::HTTPJSONInjection':
                    self._json_inject(paths, alias)

    def _json_inject(self, paths, alias):
        with open(os.path.join(TEMPLATES, 'jsoninject.json')) as f:
            template = json.load(f)
        
        swg = template['{path}']
        context = alias.split('/')[0]
        swg['post']['tags'] = [ context ]
        paths[alias] = swg
       

