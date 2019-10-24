# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import random
import string
import unittest

from streamsx.topology.tester import Tester
import streamsx.endpoint as endpoint

import os
import requests
import time
import shutil

def _rand_path():
    return ''.join(random.choices(string.ascii_uppercase, k=12))
  
class EmCommon(unittest.TestCase):
    _multiprocess_can_split_ = True
    _TK = None

    @classmethod
    def setupClass(cls):
        EmCommon._TK = endpoint.download_toolkit()

    @classmethod
    def tearDownClass(cls):
        if EmCommon._TK:
            shutil.rmtree(EmCommon._TK)

    def setUp(self):
        Tester.setup_distributed(self)
        self._base_url = os.environ['ENDPOINT_MONITOR']
        self._job_name = None
        self._monitor = os.environ.get('ENDPOINT_NAME')
        self._alias = None

    def _set_job_url(self):
        job = self.tester.submission_result.job
        if self._job_name:
            self._job_url = self._base_url + '/' + self._job_name
        else:
            self._job_url = self._base_url + '/streams/jobs/' + str(job.id)
        print('JOB URL', self._job_url)

    def _wait_for_endpoint(self):
        url = self._job_url + '/ports/info'
        for i in range(100):
            rc = requests.get(url=url, verify=False)
            if rc.status_code == 200:
                 print('JOB is monitored', self._job_url)
                 return
            time.sleep(2)
        self.fail("Job not being monitored:" + self._job_url)

    def _check_no_endpoint(self):
        url = self._job_url + '/ports/info'
        rc = requests.get(url=url, verify=False)
