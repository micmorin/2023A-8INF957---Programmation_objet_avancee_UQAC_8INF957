"""Test ZHA light."""
from  import timedelta
from  import AsyncMock, call, patch, sentinel
import pytest
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as lighting
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import DOMAIN as LIGHT_DOMAIN, FLASH_LONG, FLASH_SHORT, ColorMode
from  import CONF_ALWAYS_PREFER_XY_COLOR_MODE, CONF_GROUP_MEMBERS_ASSUME_STATE, ZHA_OPTIONS
from  import GroupMember
from  import get_zha_gateway
from  import FLASH_EFFECTS
from  import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from  import HomeAssistant
from  import entity_registry as er
import homeassistant.util.dt as dt_util
from  import async_enable_traffic, async_find_group_entity_id, async_shift_time, async_test_rejoin, async_wait_for_updates, find_entity_id, patch_zha_config, send_attributes_report, update_attribute_cache
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
from  import async_fire_time_changed
IEEE_GROUPABLE_DEVICE = '01:2d:6f:00:0a:90:69:e8'
IEEE_GROUPABLE_DEVICE2 = '02:2d:6f:00:0a:90:69:e9'
IEEE_GROUPABLE_DEVICE3 = '03:2d:6f:00:0a:90:69:e7'
LIGHT_ON_OFF = {1: {SIG_EP_PROFILE: zha.PROFILE_ID, SIG_EP_TYPE: zha.DeviceType.ON_OFF_LIGHT, SIG_EP_INPUT: [general.Basic.cluster_id, general.Identify.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: [general.Ota.cluster_id]}}
LIGHT_LEVEL = {1: {SIG_EP_PROFILE: zha.PROFILE_ID, SIG_EP_TYPE: zha.DeviceType.DIMMABLE_LIGHT, SIG_EP_INPUT: [general.Basic.cluster_id, general.LevelControl.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: [general.Ota.cluster_id]}}
LIGHT_COLOR = {1: {SIG_EP_PROFILE: zha.PROFILE_ID, SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_INPUT: [general.Basic.cluster_id, general.Identify.cluster_id, general.LevelControl.cluster_id, general.OnOff.cluster_id, lighting.Color.cluster_id], SIG_EP_OUTPUT: [general.Ota.cluster_id]}}

@pytest.fixture(autouse=True)
def light_platform_only():
    """Only set up the light and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER, Platform.BUTTON, Platform.LIGHT, Platform.SENSOR, Platform.NUMBER, Platform.SELECT)):
        yield

@pytest.fixture
async def coordinator(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Groups.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_PROFILE: zha.PROFILE_ID}}, ieee='00:15:8d:00:02:32:4f:32', nwk=0, node_descriptor=b'\xf8\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff')
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

@pytest.fixture
async def device_light_1(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.LevelControl.cluster_id, lighting.Color.cluster_id, general.Groups.cluster_id, general.Identify.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_PROFILE: zha.PROFILE_ID}}, ieee=IEEE_GROUPABLE_DEVICE, nwk=47005)
    color_cluster = zigpy_device.endpoints[1].light_color
    color_cluster.PLUGGED_ATTR_READS = {'color_capabilities': lighting.Color.ColorCapabilities.Color_temperature | lighting.Color.ColorCapabilities.XY_attributes}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

@pytest.fixture
async def device_light_2(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.LevelControl.cluster_id, lighting.Color.cluster_id, general.Groups.cluster_id, general.Identify.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_PROFILE: zha.PROFILE_ID}}, ieee=IEEE_GROUPABLE_DEVICE2, manufacturer='sengled', nwk=51102)
    color_cluster = zigpy_device.endpoints[1].light_color
    color_cluster.PLUGGED_ATTR_READS = {'color_capabilities': lighting.Color.ColorCapabilities.Color_temperature | lighting.Color.ColorCapabilities.XY_attributes}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

@pytest.fixture
async def device_light_3(hass, zigpy_device_mock, zha_device_joined):
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.LevelControl.cluster_id, lighting.Color.cluster_id, general.Groups.cluster_id, general.Identify.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_PROFILE: zha.PROFILE_ID}}, ieee=IEEE_GROUPABLE_DEVICE3, nwk=47263)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

@pytest.fixture
async def eWeLink_light(hass, zigpy_device_mock, zha_device_joined):
    """Mock eWeLink light."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.OnOff.cluster_id, general.LevelControl.cluster_id, lighting.Color.cluster_id, general.Groups.cluster_id, general.Identify.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT, SIG_EP_PROFILE: zha.PROFILE_ID}}, ieee='03:2d:6f:00:0a:90:69:e3', manufacturer='eWeLink', nwk=47005)
    color_cluster = zigpy_device.endpoints[1].light_color
    color_cluster.PLUGGED_ATTR_READS = {'color_capabilities': lighting.Color.ColorCapabilities.Color_temperature | lighting.Color.ColorCapabilities.XY_attributes, 'color_temp_physical_min': 0, 'color_temp_physical_max': 0}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    return zha_device

async def test_light_refresh(hass: HomeAssistant, zigpy_device_mock, zha_device_joined_restored) -> None:
    """Test ZHA light platform refresh."""
    zigpy_device = zigpy_device_mock(LIGHT_ON_OFF)
    on_off_cluster = zigpy_device.endpoints[1].on_off
    on_off_cluster.PLUGGED_ATTR_READS = {'on_off': 0}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    entity_id = find_entity_id(Platform.LIGHT, zha_device, hass)
    await async_enable_traffic(hass, [zha_device])
    on_off_cluster.read_attributes.reset_mock()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=20))
    await hass.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 0
    assert on_off_cluster.read_attributes.await_count == 0
    assert hass.states.get(entity_id).state == STATE_OFF
    on_off_cluster.PLUGGED_ATTR_READS = {'on_off': 1}
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=80))
    await hass.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 1
    assert on_off_cluster.read_attributes.await_count == 1
    assert hass.states.get(entity_id).state == STATE_ON
    on_off_cluster.PLUGGED_ATTR_READS = {'on_off': 0}
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=80))
    await hass.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 2
    assert on_off_cluster.read_attributes.await_count == 2
    assert hass.states.get(entity_id).state == STATE_OFF

@patch('zigpy.zcl.clusters.lighting.Color.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.Identify.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.LevelControl.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.OnOff.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@pytest.mark.parametrize(('device', 'reporting'), [(LIGHT_ON_OFF, (1, 0, 0)), (LIGHT_LEVEL, (1, 1, 0)), (LIGHT_COLOR, (1, 1, 6))])
async def test_light(hass: HomeAssistant, zigpy_device_mock, zha_device_joined_restored, device, reporting) -> None:
    """Test ZHA light platform."""
    zigpy_device = zigpy_device_mock(device)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    entity_id = find_entity_id(Platform.LIGHT, zha_device, hass)
    assert entity_id is not None
    cluster_on_off = zigpy_device.endpoints[1].on_off
    cluster_level = getattr(zigpy_device.endpoints[1], 'level', None)
    cluster_color = getattr(zigpy_device.endpoints[1], 'light_color', None)
    cluster_identify = getattr(zigpy_device.endpoints[1], 'identify', None)
    assert hass.states.get(entity_id).state == STATE_OFF
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_OFF
    await async_test_on_off_from_light(hass, cluster_on_off, entity_id)
    await async_test_on_off_from_hass(hass, cluster_on_off, entity_id)
    if cluster_identify:
        await async_test_flash_from_hass(hass, cluster_identify, entity_id, FLASH_SHORT)
    if cluster_identify:
        await async_test_flash_from_hass(hass, cluster_identify, entity_id, FLASH_LONG)
    if cluster_level:
        await async_test_level_on_off_from_hass(hass, cluster_on_off, cluster_level, entity_id)
        await async_shift_time(hass)
        await async_test_on_from_light(hass, cluster_on_off, entity_id)
        await async_test_dimmer_from_light(hass, cluster_level, entity_id, 150, STATE_ON)
    await async_test_off_from_hass(hass, cluster_on_off, entity_id)
    clusters = [c for c in (cluster_on_off, cluster_level, cluster_color) if c]
    await async_test_rejoin(hass, zigpy_device, clusters, reporting)

@pytest.mark.parametrize(('plugged_attr_reads', 'config_override', 'expected_state'), [({'color_capabilities': lighting.Color.ColorCapabilities.Hue_and_saturation}, {(ZHA_OPTIONS, CONF_ALWAYS_PREFER_XY_COLOR_MODE): False}, {}), ({'color_capabilities': lighting.Color.ColorCapabilities.Hue_and_saturation, 'current_hue': 100}, {(ZHA_OPTIONS, CONF_ALWAYS_PREFER_XY_COLOR_MODE): False}, {}), ({'color_capabilities': lighting.Color.ColorCapabilities.Hue_and_saturation, 'current_saturation': 100}, {(ZHA_OPTIONS, CONF_ALWAYS_PREFER_XY_COLOR_MODE): False}, {}), ({'color_capabilities': lighting.Color.ColorCapabilities.Hue_and_saturation, 'current_hue': 100, 'current_saturation': 100}, {(ZHA_OPTIONS, CONF_ALWAYS_PREFER_XY_COLOR_MODE): False}, {})])
async def test_light_initialization(hass: HomeAssistant, zigpy_device_mock, zha_device_joined_restored, plugged_attr_reads, config_override, expected_state) -> None:
    """Test ZHA light initialization with cached attributes and color modes."""
    zigpy_device = zigpy_device_mock(LIGHT_COLOR)
    zigpy_device.endpoints[1].light_color.PLUGGED_ATTR_READS = plugged_attr_reads
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('light', config_override):
        zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
        entity_id = find_entity_id(Platform.LIGHT, zha_device, hass)
    assert entity_id is not None

@patch('zigpy.zcl.clusters.lighting.Color.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.Identify.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.LevelControl.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.OnOff.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
async def test_transitions(hass: HomeAssistant, device_light_1, device_light_2, eWeLink_light, coordinator) -> None:
    """Test ZHA light transition code."""
    zha_gateway = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_light_1._zha_gateway = zha_gateway
    device_light_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_light_1.ieee, device_light_2.ieee]
    members = [GroupMember(device_light_1.ieee, 1), GroupMember(device_light_2.ieee, 1)]
    assert coordinator.is_coordinator
    zha_group = await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_create_zigpy_group('Test Group', members)
    await hass.async_block_till_done()
    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None
    device_1_entity_id = find_entity_id(Platform.LIGHT, device_light_1, hass)
    device_2_entity_id = find_entity_id(Platform.LIGHT, device_light_2, hass)
    eWeLink_light_entity_id = find_entity_id(Platform.LIGHT, eWeLink_light, hass)
    assert device_1_entity_id != device_2_entity_id
    group_entity_id = async_find_group_entity_id(hass, Platform.LIGHT, zha_group)
    assert hass.states.get(group_entity_id) is not None
    assert device_1_entity_id in zha_group.member_entity_ids
    assert device_2_entity_id in zha_group.member_entity_ids
    dev1_cluster_on_off = device_light_1.device.endpoints[1].on_off
    dev2_cluster_on_off = device_light_2.device.endpoints[1].on_off
    eWeLink_cluster_on_off = eWeLink_light.device.endpoints[1].on_off
    dev1_cluster_level = device_light_1.device.endpoints[1].level
    dev2_cluster_level = device_light_2.device.endpoints[1].level
    eWeLink_cluster_level = eWeLink_light.device.endpoints[1].level
    dev1_cluster_color = device_light_1.device.endpoints[1].light_color
    dev2_cluster_color = device_light_2.device.endpoints[1].light_color
    eWeLink_cluster_color = eWeLink_light.device.endpoints[1].light_color
    await async_enable_traffic(hass, [device_light_1, device_light_2])
    await async_wait_for_updates(hass)
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_OFF
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_OFF
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_OFF
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'transition': 0}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 1
    assert dev1_cluster_level.request.await_count == 1
    assert dev1_cluster_level.request.call_args == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=254, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 254
    eWeLink_cluster_on_off.request.reset_mock()
    eWeLink_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': eWeLink_light_entity_id, 'transition': 0}, blocking=True)
    assert eWeLink_cluster_on_off.request.call_count == 1
    assert eWeLink_cluster_on_off.request.await_count == 1
    assert eWeLink_cluster_on_off.request.call_args_list[0] == call(False, eWeLink_cluster_on_off.commands_by_name['on'].id, eWeLink_cluster_on_off.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert eWeLink_cluster_color.request.call_count == 0
    assert eWeLink_cluster_color.request.await_count == 0
    assert eWeLink_cluster_level.request.call_count == 1
    assert eWeLink_cluster_level.request.await_count == 1
    assert eWeLink_cluster_level.request.call_args == call(False, eWeLink_cluster_level.commands_by_name['move_to_level_with_on_off'].id, eWeLink_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=254, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    eWeLink_state = hass.states.get(eWeLink_light_entity_id)
    assert eWeLink_state.state == STATE_ON
    assert eWeLink_state.attributes['brightness'] == 254
    eWeLink_cluster_on_off.request.reset_mock()
    eWeLink_cluster_level.request.reset_mock()
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'transition': 0, 'brightness': 50}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 1
    assert dev1_cluster_level.request.await_count == 1
    assert dev1_cluster_level.request.call_args == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=50, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 50
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'transition': 3.5, 'brightness': 18, 'color_temp': 432}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 1
    assert dev1_cluster_level.request.await_count == 1
    assert dev1_cluster_level.request.call_args == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=18, transition_time=35, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=432, transition_time=35, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 18
    assert light1_state.attributes['color_temp'] == 432
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_1_entity_id, 'transition': 0}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 1
    assert dev1_cluster_level.request.await_count == 1
    assert dev1_cluster_level.request.call_args == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=0, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_OFF
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'transition': 1, 'brightness': 25, 'color_temp': 235}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 2
    assert dev1_cluster_level.request.await_count == 2
    assert dev1_cluster_level.request.call_args_list[0] == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=2, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=235, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_level.request.call_args_list[1] == call(False, dev1_cluster_level.commands_by_name['move_to_level'].id, dev1_cluster_level.commands_by_name['move_to_level'].schema, level=25, transition_time=10, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 25
    assert light1_state.attributes['color_temp'] == 235
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_1_entity_id}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_OFF
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'brightness': 25, 'color_temp': 236}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 2
    assert dev1_cluster_level.request.await_count == 2
    assert dev1_cluster_level.request.call_args_list[0] == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=2, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=236, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_level.request.call_args_list[1] == call(False, dev1_cluster_level.commands_by_name['move_to_level'].id, dev1_cluster_level.commands_by_name['move_to_level'].schema, level=25, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 25
    assert light1_state.attributes['color_temp'] == 236
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_1_entity_id}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_OFF
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'color_temp': 236}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0
    assert dev1_cluster_on_off.request.call_args == call(False, dev1_cluster_on_off.commands_by_name['on'].id, dev1_cluster_on_off.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=236, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 25
    assert light1_state.attributes['color_temp'] == 236
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_1_entity_id}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 0
    assert dev1_cluster_color.request.await_count == 0
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_OFF
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    dev2_cluster_on_off.request.reset_mock()
    dev2_cluster_color.request.reset_mock()
    dev2_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_2_entity_id, 'transition': 0, 'brightness': 100}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 0
    assert dev2_cluster_on_off.request.await_count == 0
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 1
    assert dev2_cluster_level.request.await_count == 1
    assert dev2_cluster_level.request.call_args == call(False, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=100, transition_time=1, expect_reply=True, manufacturer=None, tsn=None)
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_ON
    assert light2_state.attributes['brightness'] == 100
    dev2_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_2_entity_id}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 1
    assert dev2_cluster_on_off.request.await_count == 1
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 0
    assert dev2_cluster_level.request.await_count == 0
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_OFF
    dev2_cluster_on_off.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_2_entity_id, 'transition': 1, 'brightness': 25, 'color_temp': 235}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 0
    assert dev2_cluster_on_off.request.await_count == 0
    assert dev2_cluster_color.request.call_count == 1
    assert dev2_cluster_color.request.await_count == 1
    assert dev2_cluster_level.request.call_count == 2
    assert dev2_cluster_level.request.await_count == 2
    assert dev2_cluster_level.request.call_args_list[0] == call(False, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=2, transition_time=1, expect_reply=True, manufacturer=None, tsn=None)
    assert dev2_cluster_color.request.call_args == call(False, dev2_cluster_color.commands_by_name['move_to_color_temp'].id, dev2_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=235, transition_time=1, expect_reply=True, manufacturer=None, tsn=None)
    assert dev2_cluster_level.request.call_args_list[1] == call(False, dev2_cluster_level.commands_by_name['move_to_level'].id, dev2_cluster_level.commands_by_name['move_to_level'].schema, level=25, transition_time=10, expect_reply=True, manufacturer=None, tsn=None)
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_ON
    assert light2_state.attributes['brightness'] == 25
    assert light2_state.attributes['color_temp'] == 235
    assert light2_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev2_cluster_level.request.reset_mock()
    dev2_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_2_entity_id}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 1
    assert dev2_cluster_on_off.request.await_count == 1
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 0
    assert dev2_cluster_level.request.await_count == 0
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_OFF
    dev2_cluster_on_off.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': group_entity_id, 'transition': 1, 'brightness': 25, 'color_temp': 235}, blocking=True)
    group_on_off_cluster_handler = zha_group.endpoint[general.OnOff.cluster_id]
    group_level_cluster_handler = zha_group.endpoint[general.LevelControl.cluster_id]
    group_color_cluster_handler = zha_group.endpoint[lighting.Color.cluster_id]
    assert group_on_off_cluster_handler.request.call_count == 0
    assert group_on_off_cluster_handler.request.await_count == 0
    assert group_color_cluster_handler.request.call_count == 1
    assert group_color_cluster_handler.request.await_count == 1
    assert group_level_cluster_handler.request.call_count == 1
    assert group_level_cluster_handler.request.await_count == 1
    assert group_color_cluster_handler.request.call_args == call(False, dev2_cluster_color.commands_by_name['move_to_color_temp'].id, dev2_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=235, transition_time=10, expect_reply=True, manufacturer=None, tsn=None)
    assert group_level_cluster_handler.request.call_args == call(False, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=25, transition_time=10, expect_reply=True, manufacturer=None, tsn=None)
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_ON
    assert group_state.attributes['brightness'] == 25
    assert group_state.attributes['color_temp'] == 235
    assert group_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    group_on_off_cluster_handler.request.reset_mock()
    group_color_cluster_handler.request.reset_mock()
    group_level_cluster_handler.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_2_entity_id}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 1
    assert dev2_cluster_on_off.request.await_count == 1
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 0
    assert dev2_cluster_level.request.await_count == 0
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_ON
    dev2_cluster_on_off.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': device_2_entity_id, 'transition': 2}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 0
    assert dev2_cluster_on_off.request.await_count == 0
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 1
    assert dev2_cluster_level.request.await_count == 1
    assert dev2_cluster_level.request.call_args == call(False, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=0, transition_time=20, expect_reply=True, manufacturer=None, tsn=None)
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_OFF
    dev2_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_2_entity_id}, blocking=True)
    assert dev2_cluster_on_off.request.call_count == 0
    assert dev2_cluster_on_off.request.await_count == 0
    assert dev2_cluster_color.request.call_count == 0
    assert dev2_cluster_color.request.await_count == 0
    assert dev2_cluster_level.request.call_count == 1
    assert dev2_cluster_level.request.await_count == 1
    assert dev2_cluster_level.request.call_args == call(False, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev2_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=25, transition_time=1, expect_reply=True, manufacturer=None, tsn=None)
    light2_state = hass.states.get(device_2_entity_id)
    assert light2_state.state == STATE_ON
    dev2_cluster_level.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': eWeLink_light_entity_id, 'color_temp': 235}, blocking=True)
    assert eWeLink_cluster_on_off.request.call_count == 1
    assert eWeLink_cluster_on_off.request.await_count == 1
    assert eWeLink_cluster_color.request.call_count == 1
    assert eWeLink_cluster_color.request.await_count == 1
    assert eWeLink_cluster_level.request.call_count == 0
    assert eWeLink_cluster_level.request.await_count == 0
    assert eWeLink_cluster_on_off.request.call_args_list[0] == call(False, eWeLink_cluster_on_off.commands_by_name['on'].id, eWeLink_cluster_on_off.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=235, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    eWeLink_state = hass.states.get(eWeLink_light_entity_id)
    assert eWeLink_state.state == STATE_ON
    assert eWeLink_state.attributes['color_temp'] == 235
    assert eWeLink_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    assert eWeLink_state.attributes['min_mireds'] == 153
    assert eWeLink_state.attributes['max_mireds'] == 500

@patch('zigpy.zcl.clusters.lighting.Color.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.LevelControl.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.OnOff.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
async def test_on_with_off_color(hass: HomeAssistant, device_light_1) -> None:
    """Test turning on the light and sending color commands before on/level commands for supporting lights."""
    device_1_entity_id = find_entity_id(Platform.LIGHT, device_light_1, hass)
    dev1_cluster_on_off = device_light_1.device.endpoints[1].on_off
    dev1_cluster_level = device_light_1.device.endpoints[1].level
    dev1_cluster_color = device_light_1.device.endpoints[1].light_color
    dev1_cluster_color.PLUGGED_ATTR_READS = {'options': lighting.Color.Options.Execute_if_off}
    update_attribute_cache(dev1_cluster_color)
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'color_temp': 235}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 1
    assert dev1_cluster_on_off.request.await_count == 1
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 0
    assert dev1_cluster_level.request.await_count == 0
    assert dev1_cluster_on_off.request.call_args_list[0] == call(False, dev1_cluster_on_off.commands_by_name['on'].id, dev1_cluster_on_off.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=235, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['color_temp'] == 235
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP
    dev1_cluster_color.PLUGGED_ATTR_READS = {'options': 0}
    update_attribute_cache(dev1_cluster_color)
    await async_test_off_from_hass(hass, dev1_cluster_on_off, device_1_entity_id)
    dev1_cluster_on_off.request.reset_mock()
    dev1_cluster_level.request.reset_mock()
    dev1_cluster_color.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': device_1_entity_id, 'color_temp': 240}, blocking=True)
    assert dev1_cluster_on_off.request.call_count == 0
    assert dev1_cluster_on_off.request.await_count == 0
    assert dev1_cluster_color.request.call_count == 1
    assert dev1_cluster_color.request.await_count == 1
    assert dev1_cluster_level.request.call_count == 2
    assert dev1_cluster_level.request.await_count == 2
    assert dev1_cluster_level.request.call_args_list[0] == call(False, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].id, dev1_cluster_level.commands_by_name['move_to_level_with_on_off'].schema, level=2, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_color.request.call_args == call(False, dev1_cluster_color.commands_by_name['move_to_color_temp'].id, dev1_cluster_color.commands_by_name['move_to_color_temp'].schema, color_temp_mireds=240, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    assert dev1_cluster_level.request.call_args_list[1] == call(False, dev1_cluster_level.commands_by_name['move_to_level'].id, dev1_cluster_level.commands_by_name['move_to_level'].schema, level=254, transition_time=0, expect_reply=True, manufacturer=None, tsn=None)
    light1_state = hass.states.get(device_1_entity_id)
    assert light1_state.state == STATE_ON
    assert light1_state.attributes['brightness'] == 254
    assert light1_state.attributes['color_temp'] == 240
    assert light1_state.attributes['color_mode'] == ColorMode.COLOR_TEMP

async def async_test_on_off_from_light(hass, cluster, entity_id):
    """Test on off functionality from the light."""
    await send_attributes_report(hass, cluster, {1: 0, 0: 1, 2: 3})
    await async_wait_for_updates(hass)
    assert hass.states.get(entity_id).state == STATE_ON
    await send_attributes_report(hass, cluster, {1: 1, 0: 0, 2: 3})
    await async_wait_for_updates(hass)
    assert hass.states.get(entity_id).state == STATE_OFF

async def async_test_on_from_light(hass, cluster, entity_id):
    """Test on off functionality from the light."""
    await send_attributes_report(hass, cluster, {1: -1, 0: 1, 2: 2})
    await async_wait_for_updates(hass)
    assert hass.states.get(entity_id).state == STATE_ON

async def async_test_on_off_from_hass(hass, cluster, entity_id):
    """Test on off functionality from hass."""
    cluster.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(False, cluster.commands_by_name['on'].id, cluster.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    await async_test_off_from_hass(hass, cluster, entity_id)

async def async_test_off_from_hass(hass, cluster, entity_id):
    """Test turning off the light from Home Assistant."""
    cluster.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(False, cluster.commands_by_name['off'].id, cluster.commands_by_name['off'].schema, expect_reply=True, manufacturer=None, tsn=None)

async def async_test_level_on_off_from_hass(hass, on_off_cluster, level_cluster, entity_id, expected_default_transition: int=0):
    """Test on off functionality from hass."""
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    await async_shift_time(hass)
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
    assert on_off_cluster.request.call_count == 1
    assert on_off_cluster.request.await_count == 1
    assert level_cluster.request.call_count == 0
    assert level_cluster.request.await_count == 0
    assert on_off_cluster.request.call_args == call(False, on_off_cluster.commands_by_name['on'].id, on_off_cluster.commands_by_name['on'].schema, expect_reply=True, manufacturer=None, tsn=None)
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    await async_shift_time(hass)
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': entity_id, 'transition': 10}, blocking=True)
    assert on_off_cluster.request.call_count == 0
    assert on_off_cluster.request.await_count == 0
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert level_cluster.request.call_args == call(False, level_cluster.commands_by_name['move_to_level_with_on_off'].id, level_cluster.commands_by_name['move_to_level_with_on_off'].schema, level=254, transition_time=100, expect_reply=True, manufacturer=None, tsn=None)
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': entity_id, 'brightness': 10}, blocking=True)
    assert on_off_cluster.request.call_count == 0
    assert on_off_cluster.request.await_count == 0
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert level_cluster.request.call_args == call(False, level_cluster.commands_by_name['move_to_level_with_on_off'].id, level_cluster.commands_by_name['move_to_level_with_on_off'].schema, level=10, transition_time=int(expected_default_transition), expect_reply=True, manufacturer=None, tsn=None)
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    await async_test_off_from_hass(hass, on_off_cluster, entity_id)

async def async_test_dimmer_from_light(hass, cluster, entity_id, level, expected_state):
    """Test dimmer functionality from the light."""
    await send_attributes_report(hass, cluster, {1: level + 10, 0: level, 2: level - 10 or 22})
    await async_wait_for_updates(hass)
    assert hass.states.get(entity_id).state == expected_state
    if level == 0:
        level = None
    assert hass.states.get(entity_id).attributes.get('brightness') == level

async def async_test_flash_from_hass(hass, cluster, entity_id, flash):
    """Test flash functionality from hass."""
    cluster.request.reset_mock()
    await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': entity_id, 'flash': flash}, blocking=True)
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(False, cluster.commands_by_name['trigger_effect'].id, cluster.commands_by_name['trigger_effect'].schema, effect_id=FLASH_EFFECTS[flash], effect_variant=general.Identify.EffectVariant.Default, expect_reply=True, manufacturer=None, tsn=None)

@patch('zigpy.zcl.clusters.lighting.Color.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.Identify.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.LevelControl.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('zigpy.zcl.clusters.general.OnOff.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('homeassistant.components.zha.entity.DEFAULT_UPDATE_GROUP_FROM_CHILD_DELAY', new=0)
async def test_zha_group_light_entity(hass: HomeAssistant, device_light_1, device_light_2, device_light_3, coordinator) -> None:
    """Test the light entity for a ZHA group."""
    zha_gateway = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_light_1._zha_gateway = zha_gateway
    device_light_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_light_1.ieee, device_light_2.ieee]
    members = [GroupMember(device_light_1.ieee, 1), GroupMember(device_light_2.ieee, 1)]
    assert coordinator.is_coordinator
    zha_group = await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_create_zigpy_group('Test Group', members)
    await hass.async_block_till_done()
    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None
    device_1_entity_id = find_entity_id(Platform.LIGHT, device_light_1, hass)
    device_2_entity_id = find_entity_id(Platform.LIGHT, device_light_2, hass)
    device_3_entity_id = find_entity_id(Platform.LIGHT, device_light_3, hass)
    assert device_1_entity_id != device_2_entity_id and device_1_entity_id != device_3_entity_id
    assert device_2_entity_id != device_3_entity_id
    group_entity_id = async_find_group_entity_id(hass, Platform.LIGHT, zha_group)
    assert hass.states.get(group_entity_id) is not None
    assert device_1_entity_id in zha_group.member_entity_ids
    assert device_2_entity_id in zha_group.member_entity_ids
    assert device_3_entity_id not in zha_group.member_entity_ids
    group_cluster_on_off = zha_group.endpoint[general.OnOff.cluster_id]
    group_cluster_level = zha_group.endpoint[general.LevelControl.cluster_id]
    group_cluster_identify = zha_group.endpoint[general.Identify.cluster_id]
    dev1_cluster_on_off = device_light_1.device.endpoints[1].on_off
    dev2_cluster_on_off = device_light_2.device.endpoints[1].on_off
    dev3_cluster_on_off = device_light_3.device.endpoints[1].on_off
    dev1_cluster_level = device_light_1.device.endpoints[1].level
    await async_enable_traffic(hass, [device_light_1, device_light_2, device_light_3], enabled=False)
    await async_wait_for_updates(hass)
    assert hass.states.get(group_entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [device_light_1, device_light_2, device_light_3])
    await async_wait_for_updates(hass)
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_OFF
    assert group_state.attributes['supported_color_modes'] == [ColorMode.COLOR_TEMP, ColorMode.XY]
    assert group_state.attributes['color_mode'] is None
    await async_test_on_off_from_hass(hass, group_cluster_on_off, group_entity_id)
    await async_shift_time(hass)
    await async_test_flash_from_hass(hass, group_cluster_identify, group_entity_id, FLASH_SHORT)
    await async_shift_time(hass)
    await async_test_on_off_from_light(hass, dev1_cluster_on_off, group_entity_id)
    await async_test_level_on_off_from_hass(hass, group_cluster_on_off, group_cluster_level, group_entity_id, expected_default_transition=1)
    await async_shift_time(hass)
    await async_test_on_from_light(hass, dev1_cluster_on_off, group_entity_id)
    await async_test_dimmer_from_light(hass, dev1_cluster_level, group_entity_id, 150, STATE_ON)
    group_state = hass.states.get(group_entity_id)
    assert group_state.state == STATE_ON
    assert group_state.attributes['supported_color_modes'] == [ColorMode.COLOR_TEMP, ColorMode.XY]
    assert group_state.attributes['color_mode'] == ColorMode.XY
    await async_test_flash_from_hass(hass, group_cluster_identify, group_entity_id, FLASH_LONG)
    await async_shift_time(hass)
    assert len(zha_group.members) == 2
    await send_attributes_report(hass, dev1_cluster_on_off, {0: 1})
    await send_attributes_report(hass, dev2_cluster_on_off, {0: 1})
    await hass.async_block_till_done()
    assert hass.states.get(device_1_entity_id).state == STATE_ON
    assert hass.states.get(device_2_entity_id).state == STATE_ON
    assert hass.states.get(group_entity_id).state == STATE_ON
    await send_attributes_report(hass, dev1_cluster_on_off, {0: 0})
    await hass.async_block_till_done()
    assert hass.states.get(device_1_entity_id).state == STATE_OFF
    assert hass.states.get(device_2_entity_id).state == STATE_ON
    assert hass.states.get(group_entity_id).state == STATE_ON
    await send_attributes_report(hass, dev2_cluster_on_off, {0: 0})
    await async_wait_for_updates(hass)
    assert hass.states.get(device_1_entity_id).state == STATE_OFF
    assert hass.states.get(device_2_entity_id).state == STATE_OFF
    assert hass.states.get(group_entity_id).state == STATE_OFF
    await send_attributes_report(hass, dev1_cluster_on_off, {0: 1})
    await async_wait_for_updates(hass)
    assert hass.states.get(device_1_entity_id).state == STATE_ON
    assert hass.states.get(device_2_entity_id).state == STATE_OFF
    assert hass.states.get(group_entity_id).state == STATE_ON
    await send_attributes_report(hass, dev1_cluster_on_off, {0: 0})
    await async_wait_for_updates(hass)
    assert hass.states.get(device_1_entity_id).state == STATE_OFF
    assert hass.states.get(device_2_entity_id).state == STATE_OFF
    assert hass.states.get(group_entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_add_members([GroupMember(device_light_3.ieee, 1)])
    await send_attributes_report(hass, dev3_cluster_on_off, {0: 1})
    await async_wait_for_updates(hass)
    assert device_3_entity_id in zha_group.member_entity_ids
    assert len(zha_group.members) == 3
    assert hass.states.get(device_1_entity_id).state == STATE_OFF
    assert hass.states.get(device_2_entity_id).state == STATE_OFF
    assert hass.states.get(device_3_entity_id).state == STATE_ON
    assert hass.states.get(group_entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_remove_members([GroupMember(device_light_2.ieee, 1), GroupMember(device_light_3.ieee, 1)])
    assert len(zha_group.members) == 1
    assert hass.states.get(group_entity_id) is None
    assert device_2_entity_id not in zha_group.member_entity_ids
    assert device_3_entity_id not in zha_group.member_entity_ids
    entity_registry = er.async_get(hass)
    assert entity_registry.async_get(group_entity_id) is not None
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_add_members([GroupMember(device_light_3.ieee, 1)])
    await send_attributes_report(hass, dev3_cluster_on_off, {0: 1})
    await async_wait_for_updates(hass)
    assert len(zha_group.members) == 2
    assert hass.states.get(group_entity_id).state == STATE_ON
    await send_attributes_report(hass, dev1_cluster_on_off, {0: 0})
    await send_attributes_report(hass, dev3_cluster_on_off, {0: 0})
    await async_wait_for_updates(hass)
    assert hass.states.get(group_entity_id).state == STATE_OFF
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_add_members([GroupMember(device_light_2.ieee, 1), GroupMember(coordinator.ieee, 1)])
    await send_attributes_report(hass, dev2_cluster_on_off, {0: 1})
    await async_wait_for_updates(hass)
    assert len(zha_group.members) == 4
    assert hass.states.get(group_entity_id).state == STATE_ON
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_remove_members([GroupMember(coordinator.ieee, 1)])
    await hass.async_block_till_done()
    assert hass.states.get(group_entity_id).state == STATE_ON
    assert len(zha_group.members) == 3
    assert entity_registry.async_get(group_entity_id) is not None
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_remove_zigpy_group(zha_group.group_id)
    assert hass.states.get(group_entity_id) is None
    assert entity_registry.async_get(group_entity_id) is None

@patch('zigpy.zcl.clusters.general.OnOff.request', new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]))
@patch('homeassistant.components.zha.light.ASSUME_UPDATE_GROUP_FROM_CHILD_DELAY', new=0)
async def test_group_member_assume_state(hass: HomeAssistant, zigpy_device_mock, zha_device_joined, coordinator, device_light_1, device_light_2) -> None:
    """Test the group members assume state function."""
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('light', {(ZHA_OPTIONS, CONF_GROUP_MEMBERS_ASSUME_STATE): True}):
        zha_gateway = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
        assert zha_gateway is not None
        zha_gateway.coordinator_zha_device = coordinator
        coordinator._zha_gateway = zha_gateway
        device_light_1._zha_gateway = zha_gateway
        device_light_2._zha_gateway = zha_gateway
        member_ieee_addresses = [device_light_1.ieee, device_light_2.ieee]
        members = [GroupMember(device_light_1.ieee, 1), GroupMember(device_light_2.ieee, 1)]
        assert coordinator.is_coordinator
        zha_group = await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_create_zigpy_group('Test Group', members)
        await hass.async_block_till_done()
        assert zha_group is not None
        assert len(zha_group.members) == 2
        for member in zha_group.members:
            assert member.device.ieee in member_ieee_addresses
            assert member.group == zha_group
            assert member.endpoint is not None
        device_1_entity_id = find_entity_id(Platform.LIGHT, device_light_1, hass)
        device_2_entity_id = find_entity_id(Platform.LIGHT, device_light_2, hass)
        assert device_1_entity_id != device_2_entity_id
        group_entity_id = async_find_group_entity_id(hass, Platform.LIGHT, zha_group)
        assert hass.states.get(group_entity_id) is not None
        assert device_1_entity_id in zha_group.member_entity_ids
        assert device_2_entity_id in zha_group.member_entity_ids
        group_cluster_on_off = zha_group.endpoint[general.OnOff.cluster_id]
        await async_enable_traffic(hass, [device_light_1, device_light_2], enabled=False)
        await async_wait_for_updates(hass)
        assert hass.states.get(group_entity_id).state == STATE_UNAVAILABLE
        await async_enable_traffic(hass, [device_light_1, device_light_2])
        await async_wait_for_updates(hass)
        group_state = hass.states.get(group_entity_id)
        assert group_state.state == STATE_OFF
        group_cluster_on_off.request.reset_mock()
        await async_shift_time(hass)
        await hass.services.async_call(LIGHT_DOMAIN, 'turn_on', {'entity_id': group_entity_id}, blocking=True)
        assert hass.states.get(device_1_entity_id).state == STATE_ON
        assert hass.states.get(device_2_entity_id).state == STATE_ON
        assert hass.states.get(group_entity_id).state == STATE_ON
        await hass.services.async_call(LIGHT_DOMAIN, 'turn_off', {'entity_id': group_entity_id}, blocking=True)
        assert hass.states.get(device_1_entity_id).state == STATE_OFF
        assert hass.states.get(device_2_entity_id).state == STATE_OFF
        assert hass.states.get(group_entity_id).state == STATE_OFF
        entity_registry = er.async_get(hass)
        assert entity_registry.async_get(group_entity_id) is not None
        await 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_remove_zigpy_group(zha_group.group_id)
        assert hass.states.get(group_entity_id) is None
        assert entity_registry.async_get(group_entity_id) is None