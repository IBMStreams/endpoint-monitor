# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019
import unittest

from streamsx.topology.topology import Topology
from streamsx.topology.tester import Tester
import streamsx.endpoint as endpoint
import streamsx.spl.toolkit

import queue
import os
import requests
import time

class TestEmInject(unittest.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        Tester.setup_distributed(self)
        self._base_url = os.environ['ENDPOINT_MONITOR']
        self._tk = endpoint.download_toolkit()
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
         
    
    def _inject(self):
        self._set_job_url()
        self._wait_for_endpoint()

        url = self._job_url + self._path
        for i in range(self.N):
            data = {'seq': i}
            rc = requests.post(url=url, json=data, verify=False)
            self.assertEqual(rc.status_code, 204, str(rc))

    def test_inject(self):
        """ Test injecting.
        """
        topo = Topology()
        s = endpoint.inject(topo, name='T', context='test1')
        streamsx.spl.toolkit.add_toolkit(topo, self._tk)

        self._path = '/test1/T/ports/output/0/inject';

        self.tester = Tester(topo)
        self.tester.local_check = self._inject
        self.tester.tuple_count(s, self.N)
        self.tester.test(self.test_ctxtype, self.test_config)
