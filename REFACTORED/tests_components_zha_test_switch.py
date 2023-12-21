"""Test ZHA switch."""
from  import call, patch
import pytest
from  import DEVICE_TYPE, ENDPOINTS, INPUT_CLUSTERS, OUTPUT_CLUSTERS, PROFILE_ID
from  import ZigbeeException
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
from  import CustomDevice
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as t
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
from  import ManufacturerSpecificCluster
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import DOMAIN as SWITCH_DOMAIN
from  import GroupMember
from  import get_zha_gateway
from  import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from  import HomeAssistant
from  import HomeAssistantError
from  import async_setup_component
from  import async_enable_traffic, async_find_group_entity_id, async_test_rejoin, async_wait_for_updates, find_entity_id, send_attributes_report
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_TYPE
ON = 1
OFF = 0
IEEE_GROUPABLE_DEVICE = '01:2d:6f:00:0a:90:69:e8'
IEEE_GROUPABLE_DEVICE2 = '02:2d:6f:00:0a:90:69:e8'

@6lowpan.sixlowpan.IP6FieldLenField.addfield.fixture(autouse=True)
def switch_platform_only():
    """Only set up the switch and required base platforms to speed up tests."""
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('homeassistant.components.zha.PLATFORMS', (Platform.DEVICE_TRACKER, Platform.SENSOR, Platform.SELECT, Platform.SWITCH)):
        yield

@pytest.fixture
def zigpy_device(zigpy_device_mock):
    """Device tracker zigpy device."""
    endpoints = {1: {SIG_EP_INPUT: [general.Basic.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH}}
    return zigpy_device_mock(endpoints)

@pytest.fixture
async def coordinator(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT}}, ieee='00:15:8d:00:02:32:4f:32', nwk=0, node_descriptor=b'\xf8\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

@pytest.fixture
async def device_switch_1(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA switch platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.Groups.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH}}, ieee=IEEE_GROUPABLE_DEVICE)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    await hass.async_block_till_done()
    return zha_device

@pytest.fixture
async def device_switch_2(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA switch platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.Groups.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH}}, ieee=IEEE_GROUPABLE_DEVICE2)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    await hass.async_block_till_done()
    return zha_device

async def test_switch(hass: HomeAssistant, zha_device_joined_restored, zigpy_device) -> None:
    """Test ZHA switch platform."""
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    cluster = zigpy_device.endpoints.get(1).on_off
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SWITCH, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, cluster, {1: 0, 0: 1, 2: 2})
    assert hass.states.get(entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, cluster, {1: 1, 0: 0, 2: 2})
    assert hass.states.get(entity_id).state == STATE_OFF
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
        assert len(cluster.request.mock_calls) == 1
        assert cluster.request.call_args == call(False, ON, cluster.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
        assert len(cluster.request.mock_calls) == 1
        assert cluster.request.call_args == call(False, OFF, cluster.commands_by_name['off'].schema, expect_reply=True, manufacturer=None, tsn=None)
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, zigpy_device, [cluster], (1,))

class WindowDetectionFunctionQuirk(CustomDevice):
    """Quirk with window detection function attribute."""

    class TuyaManufCluster(CustomCluster, ManufacturerSpecificCluster):
        """Tuya manufacturer specific cluster."""
        cluster_id = 61184
        ep_attribute = 'tuya_manufacturer'
        attributes = {61185: ('window_detection_function', t.Bool), 61186: ('window_detection_function_inverter', t.Bool)}

        def __init__(self, *args, **kwargs):
            """Initialize with task."""
            super().__init__(*args, **kwargs)
            self._attr_cache.update({61185: False})
    replacement = {ENDPOINTS: {1: {PROFILE_ID: zha.PROFILE_ID, DEVICE_TYPE: zha.DeviceType.ON_OFF_SWITCH, INPUT_CLUSTERS: [general.Basic.cluster_id, TuyaManufCluster], OUTPUT_CLUSTERS: []}}}

@pytest.fixture
async def zigpy_device_tuya(hass, zigpy_device_mock, zha_device_joined):
    """Device tracker zigpy tuya device."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.ON_OFF_SWITCH}}, manufacturer='_TZE200_b6wax7g0', quirk=WindowDetectionFunctionQuirk)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    await hass.async_block_till_done()
    return zigpy_device

@6lowpan.sixlowpan.IP6FieldLenField.addfield('homeassistant.components.zha.entity.DEFAULT_UPDATE_GROUP_FROM_CHILD_DELAY', new=0)
async def test_zha_group_switch_entity(hass: HomeAssistant, device_switch_1, device_switch_2, coordinator) -> None:
    """Test the switch entity for a ZHA group."""
    zha_gateway = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_switch_1._zha_gateway = zha_gateway
    device_switch_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_switch_1.ieee, device_switch_2.ieee]
    members = [GroupMember(device_switch_1.ieee, 1), GroupMember(device_switch_2.ieee, 1)]
    zha_group = await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_create_zigpy_group('Test Group', members)
    await hass.async_block_till_done()
    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, Platform.SWITCH, zha_group)
    assert hass.states.get(entity_id) is not None
    group_cluster_on_off = zha_group.endpoint[general.OnOff.cluster_id]
    dev1_cluster_on_off = device_switch_1.device.endpoints[1].on_off
    dev2_cluster_on_off = device_switch_2.device.endpoints[1].on_off
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [device_switch_1, device_switch_2], enabled=False)
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [device_switch_1, device_switch_2])
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_OFF
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
        assert len(group_cluster_on_off.request.mock_calls) == 1
        assert group_cluster_on_off.request.call_args == call(False, ON, group_cluster_on_off.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert hass.states.get(entity_id).state == STATE_ON
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
        assert len(group_cluster_on_off.request.mock_calls) == 1
        assert group_cluster_on_off.request.call_args == call(False, OFF, group_cluster_on_off.commands_by_name['off'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, dev1_cluster_on_off, {0: 1})
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, dev2_cluster_on_off, {0: 1})
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, dev1_cluster_on_off, {0: 0})
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, dev2_cluster_on_off, {0: 0})
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, dev1_cluster_on_off, {0: 1})
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert hass.states.get(entity_id).state == STATE_ON

async def test_switch_configurable(hass: HomeAssistant, zha_device_joined_restored, zigpy_device_tuya) -> None:
    """Test ZHA configurable switch platform."""
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device_tuya)
    cluster = zigpy_device_tuya.endpoints.get(1).tuya_manufacturer
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SWITCH, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, cluster, {'window_detection_function': True})
    assert hass.states.get(entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, cluster, {'window_detection_function': False})
    assert hass.states.get(entity_id).state == STATE_OFF
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.write_attributes', return_value=[zcl_f.Status.SUCCESS, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
        assert cluster.write_attributes.mock_calls == [call({'window_detection_function': True}, manufacturer=None)]
    cluster.write_attributes.reset_mock()
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.write_attributes', return_value=[zcl_f.Status.SUCCESS, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
        assert cluster.write_attributes.mock_calls == [call({'window_detection_function': False}, manufacturer=None)]
    cluster.read_attributes.reset_mock()
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, 'homeassistant', {})
    await hass.async_block_till_done()
    await hass.services.async_call('homeassistant', 'update_entity', {'entity_id': entity_id}, blocking=True)
    assert cluster.read_attributes.call_count == 2
    assert [call(['window_detection_function'], allow_cache=False, only_cache=False, manufacturer=None), call(['window_detection_function_inverter'], allow_cache=False, only_cache=False, manufacturer=None)] == cluster.read_attributes.call_args_list
    cluster.write_attributes.reset_mock()
    cluster.write_attributes.side_effect = ZigbeeException
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield.raises(HomeAssistantError):
        await hass.services.async_call(SWITCH_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
    assert cluster.write_attributes.mock_calls == [call({'window_detection_function': False}, manufacturer=None), call({'window_detection_function': False}, manufacturer=None), call({'window_detection_function': False}, manufacturer=None)]
    cluster.write_attributes.side_effect = None
    cluster.write_attributes.reset_mock()
    cluster._attr_cache.update({61186: True})
    await hass.services.async_call(SWITCH_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
    assert cluster.write_attributes.mock_calls == [call({'window_detection_function': True}, manufacturer=None)]
    cluster.write_attributes.reset_mock()
    await hass.services.async_call(SWITCH_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
    assert cluster.write_attributes.mock_calls == [call({'window_detection_function': False}, manufacturer=None)]
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, zigpy_device_tuya, [cluster], (0,))