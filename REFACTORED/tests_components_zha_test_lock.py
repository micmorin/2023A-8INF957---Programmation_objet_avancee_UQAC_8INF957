"""Test ZHA lock."""
from  import patch
import pytest
import 6lowpan.sixlowpan.IP6FieldLenField.addfield
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as closures
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import DOMAIN as LOCK_DOMAIN
from  import STATE_LOCKED, STATE_UNAVAILABLE, STATE_UNLOCKED, Platform
from  import HomeAssistant
from  import async_enable_traffic, find_entity_id, send_attributes_report
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_TYPE
LOCK_DOOR = 0
UNLOCK_DOOR = 1
SET_PIN_CODE = 5
CLEAR_PIN_CODE = 7
SET_USER_STATUS = 9

@pytest.fixture(autouse=True)
def lock_platform_only():
    """Only set up the lock and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.DEVICE_TRACKER, Platform.LOCK, Platform.SENSOR)):
        yield

@pytest.fixture
async def lock(hass, zigpy_device_mock, zha_device_joined_restored):
    """Lock cluster fixture."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [closures.DoorLock.cluster_id, general.Basic.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zigpy.profiles.zha.DeviceType.DOOR_LOCK}})
    zha_device = await zha_device_joined_restored(zigpy_device)
    return (zha_device, zigpy_device.endpoints[1].door_lock)

async def test_lock(hass: HomeAssistant, lock) -> None:
    """Test ZHA lock platform."""
    (zha_device, cluster) = lock
    entity_id = find_entity_id(Platform.LOCK, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_UNLOCKED
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_UNLOCKED
    await send_attributes_report(hass, cluster, {1: 0, 0: 1, 2: 2})
    assert hass.states.get(entity_id).state == STATE_LOCKED
    await send_attributes_report(hass, cluster, {1: 0, 0: 2, 2: 3})
    assert hass.states.get(entity_id).state == STATE_UNLOCKED
    await async_lock(hass, cluster, entity_id)
    await async_unlock(hass, cluster, entity_id)
    await async_set_user_code(hass, cluster, entity_id)
    await async_clear_user_code(hass, cluster, entity_id)
    await async_enable_user_code(hass, cluster, entity_id)
    await async_disable_user_code(hass, cluster, entity_id)

async def async_lock(hass, cluster, entity_id):
    """Test lock functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call(LOCK_DOMAIN, 'lock', {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == LOCK_DOOR

async def async_unlock(hass, cluster, entity_id):
    """Test lock functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call(LOCK_DOMAIN, 'unlock', {'entity_id': entity_id}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == UNLOCK_DOOR

async def async_set_user_code(hass, cluster, entity_id):
    """Test set lock code functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call('zha', 'set_lock_user_code', {'entity_id': entity_id, 'code_slot': 3, 'user_code': '13246579'}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == SET_PIN_CODE
        assert cluster.request.call_args[0][3] == 2
        assert cluster.request.call_args[0][4] == closures.DoorLock.UserStatus.Enabled
        assert cluster.request.call_args[0][5] == closures.DoorLock.UserType.Unrestricted
        assert cluster.request.call_args[0][6] == '13246579'

async def async_clear_user_code(hass, cluster, entity_id):
    """Test clear lock code functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call('zha', 'clear_lock_user_code', {'entity_id': entity_id, 'code_slot': 3}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == CLEAR_PIN_CODE
        assert cluster.request.call_args[0][3] == 2

async def async_enable_user_code(hass, cluster, entity_id):
    """Test enable lock code functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call('zha', 'enable_lock_user_code', {'entity_id': entity_id, 'code_slot': 3}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == SET_USER_STATUS
        assert cluster.request.call_args[0][3] == 2
        assert cluster.request.call_args[0][4] == closures.DoorLock.UserStatus.Enabled

async def async_disable_user_code(hass, cluster, entity_id):
    """Test disable lock code functionality from hass."""
    with patch('zigpy.zcl.Cluster.request', return_value=[zcl_f.Status.SUCCESS]):
        await hass.services.async_call('zha', 'disable_lock_user_code', {'entity_id': entity_id, 'code_slot': 3}, blocking=True)
        assert cluster.request.call_count == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == SET_USER_STATUS
        assert cluster.request.call_args[0][3] == 2
        assert cluster.request.call_args[0][4] == closures.DoorLock.UserStatus.Disabled