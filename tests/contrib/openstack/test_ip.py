from testtools import TestCase
from mock import patch, call, MagicMock

import charmhelpers.contrib.openstack.ip as ip

TO_PATCH = [
    'config',
    'unit_get',
    'get_address_in_network',
    'is_clustered'
]


class TestConfig():

    def __init__(self):
        self.config = {}

    def set(self, key, value):
        self.config[key] = value

    def get(self, key):
        return self.config.get(key)


class IPTestCase(TestCase):

    def setUp(self):
        super(IPTestCase, self).setUp()
        for m in TO_PATCH:
            setattr(self, m, self._patch(m))
        self.test_config = TestConfig()
        self.config.side_effect = self.test_config.get

    def _patch(self, method):
        _m = patch('charmhelpers.contrib.openstack.ip.' + method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        return mock

    def test_resolve_address_default(self):
        self.is_clustered.return_value = False
        self.unit_get.return_value = 'unit1'
        self.get_address_in_network.return_value = 'unit1'
        self.assertEquals(ip.resolve_address(), 'unit1')
        self.unit_get.assert_called_with('public-address')
        self.config.assert_called_with('os-public-network')
        self.get_address_in_network.assert_called_with(None, 'unit1')

    def test_resolve_address_default_internal(self):
        self.is_clustered.return_value = False
        self.unit_get.return_value = 'unit1'
        self.get_address_in_network.return_value = 'unit1'
        self.assertEquals(ip.resolve_address(ip.INTERNAL), 'unit1')
        self.unit_get.assert_called_with('private-address')
        self.config.assert_called_with('os-internal-network')
        self.get_address_in_network.assert_called_with(None, 'unit1')

    def test_resolve_address_public_not_clustered(self):
        self.is_clustered.return_value = False
        self.test_config.set('os-public-network', '192.168.20.0/24')
        self.unit_get.return_value = 'unit1'
        self.get_address_in_network.return_value = '192.168.20.1'
        self.assertEquals(ip.resolve_address(), '192.168.20.1')
        self.unit_get.assert_called_with('public-address')
        self.config.assert_called_with('os-public-network')
        self.get_address_in_network.assert_called_with(
            '192.168.20.0/24',
            'unit1')

    def test_resolve_address_public_clustered(self):
        self.is_clustered.return_value = True
        self.test_config.set('os-public-network', '192.168.20.0/24')
        self.test_config.set('vip', '192.168.20.100 10.5.3.1')
        self.assertEquals(ip.resolve_address(), '192.168.20.100')

    def test_resolve_address_default_clustered(self):
        self.is_clustered.return_value = True
        self.test_config.set('vip', '10.5.3.1')
        self.assertEquals(ip.resolve_address(), '10.5.3.1')
        self.config.assert_has_calls(
            [call('os-public-network'),
             call('vip')])

    def test_resolve_address_public_clustered_inresolvable(self):
        self.is_clustered.return_value = True
        self.test_config.set('os-public-network', '192.168.20.0/24')
        self.test_config.set('vip', '10.5.3.1')
        self.assertRaises(ValueError, ip.resolve_address)

    @patch.object(ip, 'resolve_address')
    def test_canonical_url_http(self, resolve_address):
        resolve_address.return_value = 'unit1'
        configs = MagicMock()
        configs.complete_contexts.return_value = []
        self.assertTrue(ip.canonical_url(configs),
                        'http://unit1')

    @patch.object(ip, 'resolve_address')
    def test_canonical_url_https(self, resolve_address):
        resolve_address.return_value = 'unit1'
        configs = MagicMock()
        configs.complete_contexts.return_value = ['https']
        self.assertTrue(ip.canonical_url(configs),
                        'https://unit1')