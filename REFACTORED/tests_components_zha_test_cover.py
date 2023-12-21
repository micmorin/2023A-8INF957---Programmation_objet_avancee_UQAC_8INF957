"""Test ZHA cover."""
import asyncio
from  import patch
import pytest
import 6lowpan.sixlowpan.IP6FieldLenField.addfield
import 6lowpan.sixlowpan.IP6FieldLenField.addfield
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as closures
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import ATTR_CURRENT_POSITION, ATTR_CURRENT_TILT_POSITION, ATTR_TILT_POSITION, DOMAIN as COVER_DOMAIN, SERVICE_CLOSE_COVER, SERVICE_CLOSE_COVER_TILT, SERVICE_OPEN_COVER, SERVICE_OPEN_COVER_TILT, SERVICE_SET_COVER_POSITION, SERVICE_SET_COVER_TILT_POSITION, SERVICE_STOP_COVER, SERVICE_STOP_COVER_TILT, SERVICE_TOGGLE_COVER_TILT
from  import ZHA_EVENT
from  import ATTR_COMMAND, STATE_CLOSED, STATE_OPEN, STATE_UNAVAILABLE, Platform
from  import CoreState, HomeAssistant, State
from  import HomeAssistantError
from  import async_update_entity
from  import async_enable_traffic, async_test_rejoin, find_entity_id, make_zcl_header, send_attributes_report
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
from  import async_capture_events, mock_restore_cache
Default_Response = zcl_f.GENERAL_COMMANDS[zcl_f.GeneralCommand.Default_Response].schema

@pytest.fixture(autouse=True)
def cover_platform_only():
    """Only set up the cover and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.COVER, Platform.DEVICE_TRACKER, Platform.NUMBER, Platform.SELECT)):
        yield

@pytest.fixture
def zigpy_cover_device(zigpy_device_mock):
    """Zigpy cover device."""
    endpoints = {1: {SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID, SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.WINDOW_COVERING_DEVICE, SIG_EP_INPUT: [closures.WindowCovering.cluster_id], SIG_EP_OUTPUT: []}}
    return zigpy_device_mock(endpoints)

@pytest.fixture
def zigpy_cover_remote(zigpy_device_mock):
    """Zigpy cover remote device."""
    endpoints = {1: {SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID, SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.WINDOW_COVERING_CONTROLLER, SIG_EP_INPUT: [], SIG_EP_OUTPUT: [closures.WindowCovering.cluster_id]}}
    return zigpy_device_mock(endpoints)

@pytest.fixture
def zigpy_shade_device(zigpy_device_mock):
    """Zigpy shade device."""
    endpoints = {1: {SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID, SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.SHADE, SIG_EP_INPUT: [closures.Shade.cluster_id, general.LevelControl.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: []}}
    return zigpy_device_mock(endpoints)

@pytest.fixture
def zigpy_keen_vent(zigpy_device_mock):
    """Zigpy Keen Vent device."""
    endpoints = {1: {SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID, SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.LEVEL_CONTROLLABLE_OUTPUT, SIG_EP_INPUT: [general.LevelControl.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: []}}
    return zigpy_device_mock(endpoints, manufacturer='Keen Home Inc', model='SV02-612-MP-1.3')

async def test_cover(hass: HomeAssistant, zha_device_joined_restored, zigpy_cover_device) -> None:
    """Test ZHA cover platform."""
    cluster = zigpy_cover_device.endpoints.get(1).window_covering
    cluster.PLUGGED_ATTR_READS = {'current_position_lift_percentage': 65, 'current_position_tilt_percentage': 42}
    zha_device = await zha_device_joined_restored(zigpy_cover_device)
    assert cluster.read_attributes.call_count == 1
    assert 'current_position_lift_percentage' in cluster.read_attributes.call_args[0][0]
    assert 'current_position_tilt_percentage' in cluster.read_attributes.call_args[0][0]
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    await hass.async_block_till_done()
    prev_call_count = cluster.read_attributes.call_count
    await async_update_entity(hass, entity_id)
    assert cluster.read_attributes.call_count == prev_call_count + 2
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OPEN
    assert state.attributes[ATTR_CURRENT_POSITION] == 35
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 58
    await send_attributes_report(hass, cluster, {0: 0, 8: 100, 1: 1})
    assert hass.states.get(entity_id).state == STATE_CLOSED
    await send_attributes_report(hass, cluster, {0: 1, 8: 0, 1: 100})
    assert hass.states.get(entity_id).state == STATE_OPEN
    await send_attributes_report(hass, cluster, {0: 0, 9: 100, 1: 1})
    assert hass.states.get(entity_id).state == STATE_OPEN
    await send_attributes_report(hass, cluster, {0: 1, 9: 0, 1: 100})
    assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=[1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 1
        assert cluster.request.call_args[0][2].command.name == 'down_close'
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 8
        assert cluster.request.call_args[0][2].command.name == 'go_to_tilt_percentage'
        assert cluster.request.call_args[0][3] == 100
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0
        assert cluster.request.call_args[0][2].command.name == 'up_open'
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 8
        assert cluster.request.call_args[0][2].command.name == 'go_to_tilt_percentage'
        assert cluster.request.call_args[0][3] == 0
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[5, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_POSITION, {'entity_id': entity_id, 'position': 47}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 5
        assert cluster.request.call_args[0][2].command.name == 'go_to_lift_percentage'
        assert cluster.request.call_args[0][3] == 53
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[5, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_TILT_POSITION, {'entity_id': entity_id, ATTR_TILT_POSITION: 47}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 8
        assert cluster.request.call_args[0][2].command.name == 'go_to_tilt_percentage'
        assert cluster.request.call_args[0][3] == 53
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[2, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_STOP_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 2
        assert cluster.request.call_args[0][2].command.name == 'stop'
        assert cluster.request.call_args[1]['expect_reply'] is True
    with patch('zigpy.zcl.Cluster.request', return_value=[2, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_STOP_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 2
        assert cluster.request.call_args[0][2].command.name == 'stop'
        assert cluster.request.call_args[1]['expect_reply'] is True
    cluster.PLUGGED_ATTR_READS = {'current_position_lift_percentage': 0}
    await async_test_rejoin(hass, zigpy_cover_device, [cluster], (1,))
    assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=[2, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_TOGGLE_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 8
        assert cluster.request.call_args[0][2].command.name == 'go_to_tilt_percentage'
        assert cluster.request.call_args[0][3] == 100
        assert cluster.request.call_args[1]['expect_reply'] is True

async def test_cover_failures(hass: HomeAssistant, zha_device_joined_restored, zigpy_cover_device) -> None:
    """Test ZHA cover platform failure cases."""
    cluster = zigpy_cover_device.endpoints.get(1).window_covering
    cluster.PLUGGED_ATTR_READS = {'current_position_lift_percentage': None, 'current_position_tilt_percentage': 42}
    zha_device = await zha_device_joined_restored(zigpy_cover_device)
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    prev_call_count = cluster.read_attributes.call_count
    await async_update_entity(hass, entity_id)
    assert cluster.read_attributes.call_count == prev_call_count + 2
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    await hass.async_block_till_done()
    await send_attributes_report(hass, cluster, {0: 0, 8: 100, 1: 1})
    assert hass.states.get(entity_id).state == STATE_CLOSED
    await send_attributes_report(hass, cluster, {0: 1, 8: 0, 1: 100})
    assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.down_close.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to close cover'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.down_close.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to close cover tilt'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.up_open.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to open cover'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.up_open.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to open cover tilt'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER_TILT, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.go_to_lift_percentage.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to set cover position'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_POSITION, {'entity_id': entity_id, 'position': 47}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.go_to_lift_percentage.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to set cover tilt position'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_TILT_POSITION, {'entity_id': entity_id, 'tilt_position': 42}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.go_to_tilt_percentage.id
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.stop.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError, match='Failed to stop cover'):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_STOP_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][1] == closures.WindowCovering.ServerCommandDefs.stop.id

async def test_shade(hass: HomeAssistant, zha_device_joined_restored, zigpy_shade_device) -> None:
    """Test ZHA cover platform for shade device type."""
    zha_device = await zha_device_joined_restored(zigpy_shade_device)
    cluster_on_off = zigpy_shade_device.endpoints.get(1).on_off
    cluster_level = zigpy_shade_device.endpoints.get(1).level
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    await hass.async_block_till_done()
    await send_attributes_report(hass, cluster_on_off, {8: 0, 0: False, 1: 1})
    assert hass.states.get(entity_id).state == STATE_CLOSED
    await send_attributes_report(hass, cluster_on_off, {8: 0, 0: True, 1: 1})
    assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.down_close.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_on_off.request.call_count == 1
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 0
        assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=[1, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_CLOSE_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_on_off.request.call_count == 1
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 0
        assert hass.states.get(entity_id).state == STATE_CLOSED
    assert ATTR_CURRENT_POSITION not in hass.states.get(entity_id).attributes
    await send_attributes_report(hass, cluster_level, {0: 0})
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.up_open.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_on_off.request.call_count == 1
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 1
        assert hass.states.get(entity_id).state == STATE_CLOSED
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=general.LevelControl.ServerCommandDefs.stop.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_STOP_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_level.request.call_count == 1
        assert cluster_level.request.call_args[0][0] is False
        assert cluster_level.request.call_args[0][1] == general.LevelControl.ServerCommandDefs.stop.id
        assert hass.states.get(entity_id).state == STATE_CLOSED
    with patch('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_on_off.request.call_count == 1
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 1
        assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', return_value=Default_Response(command_id=closures.WindowCovering.ServerCommandDefs.go_to_lift_percentage.id, status=zcl_f.Status.UNSUP_CLUSTER_COMMAND)):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_POSITION, {'entity_id': entity_id, 'position': 47}, blocking=True)
        assert cluster_level.request.call_count == 1
        assert cluster_level.request.call_args[0][0] is False
        assert cluster_level.request.call_args[0][1] == 4
        assert int(cluster_level.request.call_args[0][3] * 100 / 255) == 47
        assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == 0
    with patch('zigpy.zcl.Cluster.request', return_value=[5, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(COVER_DOMAIN, SERVICE_SET_COVER_POSITION, {'entity_id': entity_id, 'position': 47}, blocking=True)
        assert cluster_level.request.call_count == 1
        assert cluster_level.request.call_args[0][0] is False
        assert cluster_level.request.call_args[0][1] == 4
        assert int(cluster_level.request.call_args[0][3] * 100 / 255) == 47
        assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == 47
    await send_attributes_report(hass, cluster_level, {8: 0, 0: 100, 1: 1})
    assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == int(100 * 100 / 255)
    await async_test_rejoin(hass, zigpy_shade_device, [cluster_level, cluster_on_off], (1,))
    assert hass.states.get(entity_id).state == STATE_OPEN
    with patch('zigpy.zcl.Cluster.request', side_effect=asyncio.TimeoutError):
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_STOP_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_level.request.call_count == 3
        assert cluster_level.request.call_args[0][0] is False
        assert cluster_level.request.call_args[0][1] in (3, 7)

async def test_shade_restore_state(hass: HomeAssistant, zha_device_restored, zigpy_shade_device) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(hass, (State('cover.fakemanufacturer_fakemodel_shade', STATE_OPEN, {ATTR_CURRENT_POSITION: 50}),))
    hass.state = CoreState.starting
    zha_device = await zha_device_restored(zigpy_shade_device)
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_OPEN
    assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == 50

async def test_cover_restore_state(hass: HomeAssistant, zha_device_restored, zigpy_cover_device) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(hass, (State('cover.fakemanufacturer_fakemodel_cover', STATE_OPEN, {ATTR_CURRENT_POSITION: 50, ATTR_CURRENT_TILT_POSITION: 42}),))
    hass.state = CoreState.starting
    zha_device = await zha_device_restored(zigpy_cover_device)
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_OPEN
    assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == 50
    assert hass.states.get(entity_id).attributes[ATTR_CURRENT_TILT_POSITION] == 42

async def test_keen_vent(hass: HomeAssistant, zha_device_joined_restored, zigpy_keen_vent) -> None:
    """Test keen vent."""
    zha_device = await zha_device_joined_restored(zigpy_keen_vent)
    cluster_on_off = zigpy_keen_vent.endpoints.get(1).on_off
    cluster_level = zigpy_keen_vent.endpoints.get(1).level
    entity_id = find_entity_id(Platform.COVER, zha_device, hass)
    assert entity_id is not None
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    await hass.async_block_till_done()
    await send_attributes_report(hass, cluster_on_off, {8: 0, 0: False, 1: 1})
    assert hass.states.get(entity_id).state == STATE_CLOSED
    p1 = patch.object(cluster_on_off, 'request', side_effect=asyncio.TimeoutError)
    p2 = patch.object(cluster_level, 'request', return_value=[4, 0])
    with p1, p2:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        assert cluster_on_off.request.call_count == 3
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 1
        assert cluster_level.request.call_count == 1
        assert hass.states.get(entity_id).state == STATE_CLOSED
    p1 = patch.object(cluster_on_off, 'request', return_value=[1, 0])
    p2 = patch.object(cluster_level, 'request', return_value=[4, 0])
    with p1, p2:
        await hass.services.async_call(COVER_DOMAIN, SERVICE_OPEN_COVER, {'entity_id': entity_id}, blocking=True)
        await asyncio.sleep(0)
        assert cluster_on_off.request.call_count == 1
        assert cluster_on_off.request.call_args[0][0] is False
        assert cluster_on_off.request.call_args[0][1] == 1
        assert cluster_level.request.call_count == 1
        assert hass.states.get(entity_id).state == STATE_OPEN
        assert hass.states.get(entity_id).attributes[ATTR_CURRENT_POSITION] == 100

async def test_cover_remote(hass: HomeAssistant, zha_device_joined_restored, zigpy_cover_remote) -> None:
    """Test ZHA cover remote."""
    await zha_device_joined_restored(zigpy_cover_remote)
    cluster = zigpy_cover_remote.endpoints[1].out_clusters[closures.WindowCovering.cluster_id]
    zha_events = async_capture_events(hass, ZHA_EVENT)
    hdr = make_zcl_header(0, global_command=False)
    cluster.handle_message(hdr, [])
    await hass.async_block_till_done()
    assert len(zha_events) == 1
    assert zha_events[0].data[ATTR_COMMAND] == 'up_open'
    hdr = make_zcl_header(1, global_command=False)
    cluster.handle_message(hdr, [])
    await hass.async_block_till_done()
    assert len(zha_events) == 2
    assert zha_events[1].data[ATTR_COMMAND] == 'down_close'