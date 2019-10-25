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
import streamsx.spl.op as op

import os
import requests

from em_common import EmCommon, _rand_path

class TestEmSPL(EmCommon):

    def setUp(self):
        super(TestEmSPL, self).setUp()

    def test_spl_ops(self):
        topo = Topology()
        streamsx.spl.toolkit.add_toolkit(topo, TestEmSPL._TK)

        context = _rand_path()
        name = _rand_path()
        schema = StreamSchema('tuple<int32 a, rstring b, boolean c>')

        params = {}
        params['port'] = 0
        params['context'] = context
        if self._monitor:
            params['sslAppConfigName'] = self._monitor + '-stream-certs'

        print('DDDD', params)

        inject = op.Source(topo, 'com.ibm.streamsx.inet.rest::HTTPTupleInjection', schema, params, name)

        self._path = '/' + context + '/' + name + '/ports/output/0/inject'
        self._alias = '/' + context + '/' + name + '/inject'

        self.tester = Tester(topo)
        self.tester.local_check = self._form_inject
        self.tester.contents(inject.stream, [{'a':42, 'b':'HHGTTG', 'c':True}, {'a':93, 'b':'ABCDE', 'c':False}])
        self.tester.test(self.test_ctxtype, self.test_config)

        self._check_no_endpoint()

    def _form_inject(self):
        self._set_job_url()
        self._wait_for_endpoint()

        # switch between the full traditional URL and the alias created
        # by the endpoint monitor
        url_full = self._job_url + self._path
        url_alias = self._job_url + self._alias
        url_form = url_alias[0:-1*len('/inject')] + '/form'

        data = {'a':42, 'b':'HHGTTG', 'c':True}

        print('DDD', url_full)
        rc = requests.post(url=url_full, data=data, verify=False)
        print('DDD', rc)
        self.assertEqual(rc.status_code, 204, str(rc))

        data = {'a':93, 'b':'ABCDE', 'c':False}
        rc = requests.post(url=url_alias, data=data, verify=False)
        self.assertEqual(rc.status_code, 204, str(rc))

        rc = requests.get(url=url_form, verify=False)
        self.assertEqual(rc.status_code, 200, str(rc))

