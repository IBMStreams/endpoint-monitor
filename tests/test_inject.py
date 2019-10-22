# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import random
import string
import unittest

from streamsx.topology.topology import Topology
from streamsx.topology.tester import Tester
import streamsx.endpoint as endpoint
import streamsx.spl.toolkit

import queue
import os
import requests
import time

def _rand_path():
    return ''.join(random.choices(string.ascii_uppercase, k=8))
  
class TestEmInject(unittest.TestCase):
    _multiprocess_can_split_ = True
    _TK = None

    @classmethod
    def setupClass(cls):
        TestEmInject._TK = endpoint.download_toolkit()

    def setUp(self):
        Tester.setup_distributed(self)
        self._base_url = os.environ['ENDPOINT_MONITOR']
        self._job_name = None
        self.N = 163

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
    
    def _inject(self):
        self._set_job_url()
        self._wait_for_endpoint()

        url = self._job_url + self._path
        for i in range(self.N):
            data = {'seq': i}
            rc = requests.post(url=url, json=data, verify=False)
            self.assertEqual(rc.status_code, 204, str(rc))

    def test_inject(self):
        self._monitor = None
        self._inject_tester()

    @unittest.skipUnless('ENDPOINT_NAME' in os.environ, "Need ENDPOINT_NAME set for HTTPS")
    def test_inject_https(self):
        self._monitor = os.environ['ENDPOINT_NAME']
        self._inject_tester()
        
    def _inject_tester(self):
        """ Test injecting.
        """
        topo = Topology()
        context = _rand_path()
        name = _rand_path()
        s = endpoint.inject(topo, name=name, context=context, monitor=self._monitor)
        streamsx.spl.toolkit.add_toolkit(topo, TestEmInject._TK)

        self._path = '/' + context + '/' + name + '/ports/output/0/inject';

        self.tester = Tester(topo)
        self.tester.local_check = self._inject
        self.tester.tuple_count(s, self.N)
        self.tester.contents(s, [{'seq':i} for i in range(self.N)])
        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()
