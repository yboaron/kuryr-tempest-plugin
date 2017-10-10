# Copyright 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testtools

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.lib.common.utils import data_utils

from kuryr_tempest_plugin.tests.scenario import base

LOG = logging.getLogger(__name__)
CONF = config.CONF


class TestCrossPingScenario(base.BaseKuryrScenarioTest):

    @classmethod
    def skip_checks(cls):
        super(TestCrossPingScenario, cls).skip_checks()
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @decorators.idempotent_id('bddf5441-1244-449d-a125-b5fddfb1a1a8')
    def test_vm_pod_ping(self):
        keypair = self.create_keypair()
        security_groups = [
            {'name': self._create_security_group()['name']}
        ]
        server = self.create_server(name=data_utils.rand_name(prefix='kuryr'),
                                    key_name=keypair['name'],
                                    security_groups=security_groups)
        fip = self.create_floating_ip(server)

        pod_name, pod = self.create_pod()
        self.addCleanup(self.delete_pod, pod_name, pod)
        pod_fip = self.assign_fip_to_pod(pod_name)

        ssh_client = self.get_remote_client(fip['floating_ip_address'],
                                            private_key=keypair['private_key'])
        cmd = ("ping -c1 -w1 %s &> /dev/null; echo $?" %
               pod_fip['floatingip']['floating_ip_address'])

        try:
            result = ssh_client.exec_command(cmd)
            if result:
                msg = ('Failed while trying to ping. Could not ping '
                       'from host "%s" to "%s".' % (
                           fip['floating_ip_address'],
                           pod_fip['floatingip']['floating_ip_address']))
            self.assertEqual('0', result.rstrip('\n'))
        except exceptions.SSHExecCommandFailed:
            LOG.error("Couldn't ping server")