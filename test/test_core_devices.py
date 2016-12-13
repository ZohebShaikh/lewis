# -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

import unittest
from . import assertRaisesNothing, TestWithPackageStructure

from plankton.core.devices import is_device, is_adapter, \
    DeviceRegistry, DeviceBuilder, DeviceBase
from plankton.core.exceptions import PlanktonException
from plankton.devices import Device, StateMachineDevice
from plankton.adapters import Adapter
from plankton.adapters.stream import StreamAdapter

from uuid import uuid4

from types import ModuleType


class TestIsDevice(unittest.TestCase):
    def test_not_a_type_returns_false(self):
        self.assertFalse(is_device(0.0))
        self.assertFalse(is_device(None))

    def test_arbitrary_types_fail(self):
        self.assertFalse(is_device(type(3.0)))
        self.assertFalse(is_device(DeviceBuilder))

    def test_device_bases_are_ignored(self):
        self.assertFalse(is_device(DeviceBase))
        self.assertFalse(is_device(Device))
        self.assertFalse(is_device(StateMachineDevice))

    def test_device_types_work(self):
        class DummyDevice(Device):
            pass

        class DummyStatemachineDevice(StateMachineDevice):
            pass

        self.assertTrue(is_device(DummyDevice))
        self.assertTrue(is_device(DummyStatemachineDevice))


class TestIsAdapter(unittest.TestCase):
    def test_not_a_type_returns_false(self):
        self.assertFalse(is_adapter(0.0))
        self.assertFalse(is_adapter(None))

    def test_arbitrary_types_fail(self):
        self.assertFalse(is_adapter(type(3.0)))
        self.assertFalse(is_adapter(DeviceBuilder))

    def test_adapter_base_is_ignored(self):
        self.assertFalse(is_adapter(Adapter))
        self.assertFalse(is_adapter(StreamAdapter))

    def test_adapter_types_work(self):
        class DummyAdapter(Adapter):
            pass

        self.assertTrue(is_adapter(DummyAdapter))


class TestDeviceBuilderSimpleModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyDevice(Device):
            pass

        class DummyAdapter(Adapter):
            protocol = 'dummy'

        cls.module = ModuleType('simple_dummy_module')
        cls.module.DummyDevice = DummyDevice
        cls.module.DummyAdapter = DummyAdapter

    def test_init(self):
        assertRaisesNothing(self, DeviceBuilder, self.module)

        builder = DeviceBuilder(self.module)
        self.assertEqual(builder.name, self.module.__name__)

    def test_defaults(self):
        builder = DeviceBuilder(self.module)

        self.assertIs(builder.default_device_type, self.module.DummyDevice)
        self.assertIs(builder.default_protocol, self.module.DummyAdapter.protocol)

    def test_setups(self):
        builder = DeviceBuilder(self.module)

        setups = builder.setups
        self.assertEqual(len(setups), 1)
        self.assertIn('default', setups)

    def test_protocols(self):
        builder = DeviceBuilder(self.module)

        protocols = builder.protocols
        self.assertEqual(len(protocols), 1)
        self.assertIn('dummy', protocols)

    def test_create_device(self):
        builder = DeviceBuilder(self.module)

        device = builder.create_device()
        self.assertIsInstance(device, self.module.DummyDevice)

        self.assertRaises(PlanktonException, builder.create_device, 'invalid_setup')

    def test_create_interface(self):
        builder = DeviceBuilder(self.module)

        device = builder.create_device()

        self.assertIsInstance(builder.create_interface(device=device), self.module.DummyAdapter)
        self.assertIsInstance(
            builder.create_interface('dummy', device=device), self.module.DummyAdapter)

        self.assertRaises(PlanktonException, builder.create_interface, 'invalid_protocol')


class TestDeviceBuilderMultipleDevicesAndProtocols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyDevice(Device):
            pass

        class OtherDummyDevice(Device):
            pass

        class DummyAdapter(Adapter):
            protocol = 'dummy'

        class OtherDummyAdapter(Adapter):
            protocol = 'other_dummy'

        cls.module = ModuleType('multiple_devices_dummy_module')
        cls.module.DummyDevice = DummyDevice
        cls.module.OtherDummyDevice = OtherDummyDevice
        cls.module.DummyAdapter = DummyAdapter
        cls.module.OtherDummyAdapter = OtherDummyAdapter

    def test_defaults(self):
        builder = DeviceBuilder(self.module)

        self.assertIs(builder.default_device_type, None)
        self.assertIs(builder.default_protocol, None)

    def test_setups(self):
        builder = DeviceBuilder(self.module)

        setups = builder.setups
        self.assertEqual(len(setups), 1)
        self.assertIn('default', setups)

    def test_protocols(self):
        builder = DeviceBuilder(self.module)

        protocols = builder.protocols
        self.assertEqual(len(protocols), 2)
        self.assertIn('dummy', protocols)
        self.assertIn('other_dummy', protocols)

    def test_create_device(self):
        builder = DeviceBuilder(self.module)

        self.assertRaises(PlanktonException, builder.create_device)
        self.assertRaises(PlanktonException, builder.create_device, 'default')


class TestDeviceBuilderComplexModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyDevice(Device):
            pass

        class OtherDummyDevice(Device):
            pass

        class DummyAdapter(Adapter):
            protocol = 'dummy'

        class OtherDummyAdapter(Adapter):
            protocol = 'other_dummy'

        cls.module = ModuleType('complex_dummy_module')
        cls.module.DummyDevice = DummyDevice
        cls.module.OtherDummyDevice = OtherDummyDevice
        cls.module.interfaces = ModuleType('interfaces')
        cls.module.interfaces.dummy = ModuleType('dummy')
        cls.module.interfaces.dummy.DummyAdapter = DummyAdapter
        cls.module.interfaces.other_dummy = ModuleType('other_dummy')
        cls.module.interfaces.other_dummy.OtherDummyAdapter = OtherDummyAdapter
        cls.module.setups = ModuleType('setups')
        cls.module.setups.default = ModuleType('default')
        cls.module.setups.default.device_type = DummyDevice
        cls.module.setups.other = ModuleType('other')
        cls.module.setups.other.device_type = OtherDummyDevice

    def test_defaults(self):
        builder = DeviceBuilder(self.module)

        self.assertIs(builder.default_device_type, None)
        self.assertIs(builder.default_protocol, None)

    def test_setups(self):
        builder = DeviceBuilder(self.module)

        setups = builder.setups
        self.assertEqual(len(setups), 2)
        self.assertIn('default', setups)
        self.assertIn('other', setups)

    def test_create_device(self):
        builder = DeviceBuilder(self.module)

        self.assertIsInstance(builder.create_device(), self.module.DummyDevice)
        self.assertIsInstance(builder.create_device('default'), self.module.DummyDevice)
        self.assertIsInstance(builder.create_device('other'), self.module.OtherDummyDevice)


class TestDeviceBuilderWithDuplicateProtocols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyAdapter(Adapter):
            protocol = 'dummy'

        class DummyAdapterTwo(Adapter):
            protocol = 'dummy'

        cls.module = ModuleType('simple_dummy_module')
        cls.module.DummyAdapter = DummyAdapter
        cls.module.DummyAdapterTwo = DummyAdapterTwo

    def test_init_fails(self):
        self.assertRaises(RuntimeError, DeviceBuilder, self.module)


class TestDeviceRegistry(TestWithPackageStructure):
    def test_init(self):
        assertRaisesNothing(self, DeviceRegistry, self._tmp_package_name)
        self.assertRaises(PlanktonException, DeviceRegistry, str(uuid4()))

    def test_devices(self):
        registry = DeviceRegistry(self._tmp_package_name)

        devices = registry.devices
        self.assertEqual(len(devices), 2)
        self.assertIn('some_file', devices)
        self.assertIn('some_dir', devices)

    def test_device_builder(self):
        registry = DeviceRegistry(self._tmp_package_name)

        builder = registry.device_builder('some_file')
        self.assertEquals(builder.name, 'some_file')

        self.assertRaises(PlanktonException, registry.device_builder, 'invalid_device')
