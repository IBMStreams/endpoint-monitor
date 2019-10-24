# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import unittest

from streamsx.topology.topology import Topology
from streamsx.topology.context import JobConfig
from streamsx.topology.schema import StreamSchema
from streamsx.topology.tester import Tester
import streamsx.endpoint as endpoint
import streamsx.spl.toolkit

import os
import requests

from em_common import EmCommon, _rand_path

class TestEmInject(EmCommon):

    def setUp(self):
        super(TestEmInject, self).setUp()
        self.N = 163
        self.K = 'seq'

    def _inject(self):
        self._set_job_url()
        self._wait_for_endpoint()

        # switch between the full traditional URL and the alias created
        # by the endpoint monitor
        url_full = self._job_url + self._path
        url_alias = self._job_url + self._alias if self._alias else None
        for i in range(self.N):
            data = {self.K: i}
            url = url_alias if url_alias and i % 2 == 0 else url_full
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

        self._path = '/' + context + '/' + name + '/ports/output/0/inject'
        self._alias = '/' + context + '/' + name + '/inject'

        self.tester = Tester(topo)
        self.tester.local_check = self._inject
        self.tester.tuple_count(s, self.N)
        self.tester.contents(s, [{self.K:i} for i in range(self.N)])
        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()

    def test_multi_inject(self):
        self._multi_injection()

    def test_multi_servers(self):
        self._multi_injection(raw_overlay = {'deploymentConfig': {'fusionScheme': 'legacy'}})

    def _multi_injection(self, raw_overlay=None):
        topo = Topology()
        streamsx.spl.toolkit.add_toolkit(topo, TestEmInject._TK)
        context = _rand_path()
        name = _rand_path()
        job_name = _rand_path()
        s1 = endpoint.inject(topo, name=name+'N1', context=context+'C1', monitor=self._monitor)
        s2 = endpoint.inject(topo, name=name+'N2', context=context+'C2', monitor=self._monitor)
        jc = JobConfig()
        self._job_name = _rand_path()
        jc.job_name = self._job_name
        jc.add(self.test_config)
        # Force separate PEs for the inject operators
   
        if raw_overlay:
            jc.raw_overlay = raw_overlay
        else:
            s1.colocate(s2)

        self._path = '/' + context + 'C1/' + name + 'N1/ports/output/0/inject'

        self.tester = Tester(topo)
        self.tester.local_check = self._multi_inject
        self.tester.contents(s1, [{'seq1':i} for i in range(self.N)])
        self.tester.contents(s2, [{'seq2':i} for i in range(self.N)])

        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()

    def _multi_inject(self):
        self.K = 'seq1'
        self._inject()

        self.K = 'seq2'
        self._path = self._path.replace('N1/', 'N2/').replace('C1/', 'C2/')
        self._inject()

    def test_form_inject(self):
        topo = Topology()
        context = _rand_path()
        name = _rand_path()
        schema = StreamSchema('tuple<int32 a, rstring b, boolean c>')
        s = endpoint.inject(topo, name=name, context=context, monitor=self._monitor, schema=schema)
        streamsx.spl.toolkit.add_toolkit(topo, TestEmInject._TK)

        self._path = '/' + context + '/' + name + '/ports/output/0/inject'
        self._alias = '/' + context + '/' + name + '/inject'

        self.tester = Tester(topo)
        self.tester.local_check = self._form_inject
        s.print()
        self.tester.contents(s, [{'a':42, 'b':'HHGTTG', 'c':True}, {'a':93, 'b':'ABCDE', 'c':False}])
        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()

    def _form_inject(self):
        self._set_job_url()
        self._wait_for_endpoint()

        # switch between the full traditional URL and the alias created
        # by the endpoint monitor
        url_full = self._job_url + self._path
        url_alias = self._job_url + self._alias

        data = {'a':42, 'b':'HHGTTG', 'c':True}

        rc = requests.post(url=url_full, data=data, verify=False)
        print('DDD', 'FULL', rc)
        self.assertEqual(rc.status_code, 204, str(rc))

        data = {'a':93, 'b':'ABCDE', 'c':False}
        rc = requests.post(url=url_alias, data=data, verify=False)
        print('DDD', 'ALIAS', rc)
        self.assertEqual(rc.status_code, 204, str(rc))
