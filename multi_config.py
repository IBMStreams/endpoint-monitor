# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import os

class MultiConfig(object):
    """Configurator that invokes multiple configurators.
    """
    def __init__(self, *configs):
        self._configs = configs

    def clean(self):
        for cfg in self._configs:
            cfg.clean()
  
    def create(self, jobid, job_config):
        for cfg in self._configs:
            cfg.create(jobid, job_config)

    def delete(self, jobid, job_config):
        for cfg in self._configs:
            cfg.delete(jobid, job_config)

    def update(self, jobid, old_job_config, job_config):
        for cfg in self._configs:
            cfg.update(jobid, old_job_config, job_config)
