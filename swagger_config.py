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

    def _update_jobs_file():
        cfn = 'jobs.js'
        tfn = cfn + '.tmp'
        fcfn = os.path.join(self._location, cfn)
        ftfn = os.path.join(self._location, tfn)
        with open(ftfn, 'w') as f:
            for job in self._jobs:
                pass
        os.rename(ftfn, fcfn)

    def _job_name(jobid, job_config):
        if job_config.name == job_config.applicationName + '_' + jobid:
            return 'job-%s' % jobid
        else:
            return job_config.name
        
    def clean(self):
        # Remove all -streams-job-%s.conf
        self._jobs = {}
        self._update_jobs_file()
  
    def create(self, jobid, job_config):
        self._create_swagger_file(jobid, job_config)
        #job_config.swagger_file = self._write_file(jobid, location, job_config)
        self._update_jobs_file()

    def delete(self, jobid, job_config):
        if hasattr(job_config, 'swagger_file'):
            os.remove(job_config.swagger_file)
        self._update_jobs_file()

    def update(self, jobid, old_job_config, job_config):
        self.delete(jobid, old_job_config)
        self.create(jobid, job_config)

    def _create_swagger_file(jobid, job_config):
        name = self._job_name(jobid, job_config)
        fname = name + '.json'
        tname = fname + '.tmp'
        with open(tname, 'w') as f:
            swg = self._job_swagger(name, jobid, job_config)
            json.dump(swg, f)
        os.rename(tname, fname)

    def _job_swagger(name, jobid, job_config):
        with open(os.path.join(TEMPLATES, 'job.json')) as j:
            swg = json.load(j)

        desc = swg['info']['description']
        swg['info']['description'] = desc.format(
            job_id=jobid, job_name=job_config.name, instance_id=self._instance)
        title = swg['info']['title']
        swg['info']['title'] = title.format(job_name=name)
        return swg

