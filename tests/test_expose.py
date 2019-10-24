# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2019

import unittest

from streamsx.topology.topology import Topology
from streamsx.topology.context import JobConfig
from streamsx.topology.tester import Tester
import streamsx.endpoint as endpoint
import streamsx.spl.toolkit

import os
import requests
import time

from em_common import EmCommon, _rand_path

class TestEmExpose(EmCommon):

    def setUp(self):
        super(TestEmExpose, self).setUp()

    def _access(self):
        self._set_job_url()
        self._wait_for_endpoint()
        time.sleep(2)

        url_full = self._job_url + self._path
        resp = requests.get(url=url_full, verify=False)
        self.assertEqual(resp.status_code, 200, str(resp))
        data = resp.json()
        self.assertEqual(data, [{'seq': 17}, {'seq': 18}, {'seq': 19}])

        url_alias = self._job_url + self._alias
        resp = requests.get(url=url_alias, verify=False)
        self.assertEqual(resp.status_code, 200, str(resp))
        data = resp.json()
        self.assertEqual(data, [{'seq': 17}, {'seq': 18}, {'seq': 19}])

    def test_expose(self):
        topo = Topology()
        streamsx.spl.toolkit.add_toolkit(topo, TestEmExpose._TK)
        s = topo.source([{'seq':i} for i in range(20)])
        s = s.as_json()

        context = _rand_path()
        name = _rand_path()

        endpoint.expose(s.last(3), name=name, context=context, monitor=self._monitor)

        self._path = '/' + context + '/' + name + '/ports/input/0/tuples';
        self._alias = '/' + context + '/' + name + '/tuples';

        self.tester = Tester(topo)
        self.tester.local_check = self._access
        self.tester.tuple_count(s, 20)
        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()
