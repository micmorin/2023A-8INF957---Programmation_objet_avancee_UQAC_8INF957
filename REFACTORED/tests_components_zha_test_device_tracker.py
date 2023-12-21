"""Test ZHA Device Tracker."""
from  import timedelta
import time
from  import patch
import pytest
import 6lowpan.sixlowpan.IP6FieldLenField.addfield
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
from  import SourceType
from  import SMARTTHINGS_ARRIVAL_SENSOR_DEVICE_TYPE
from  import STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE, Platform
from  import HomeAssistant
import homeassistant.util.dt as dt_util
from  import async_enable_traffic, async_test_rejoin, find_entity_id, send_attributes_report
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
from  import async_fire_time_changed

@pytest.fixture(autouse=True)
def device_tracker_platforms_only():
    """Only set up the device_tracker platforms and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.DEVICE_TRACKER, Platform.BUTTON, Platform.SELECT, Platform.NUMBER, Platform.BINARY_SENSOR, Platform.SENSOR)):
        yield

@pytest.fixture
def zigpy_device_dt(zigpy_device_mock):
    """Device tracker zigpy device."""
    endpoints = {1: {SIG_EP_INPUT: [general.Basic.cluster_id, general.PowerConfiguration.cluster_id, general.Identify.cluster_id, general.PollControl.cluster_id, general.BinaryInput.cluster_id], SIG_EP_OUTPUT: [general.Identify.cluster_id, general.Ota.cluster_id], SIG_EP_TYPE: SMARTTHINGS_ARRIVAL_SENSOR_DEVICE_TYPE, SIG_EP_PROFILE: zigpy.profiles.zha.PROFILE_ID}}
    return zigpy_device_mock(endpoints)

async def test_device_tracker(hass: HomeAssistant, zha_device_joined_restored, zigpy_device_dt) -> None:
    """Test ZHA device tracker platform."""
    zha_device = await zha_device_joined_restored(zigpy_device_dt)
    cluster = zigpy_device_dt.endpoints.get(1).power
    entity_id = find_entity_id(Platform.DEVICE_TRACKER, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_NOT_HOME
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    zigpy_device_dt.last_seen = time.time() - 120
    next_update = dt_util.utcnow() + timedelta(seconds=30)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done()
    await async_enable_traffic(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_NOT_HOME
    await send_attributes_report(hass, cluster, {0: 0, 32: 23, 33: 200, 1: 2})
    zigpy_device_dt.last_seen = time.time() + 10
    next_update = dt_util.utcnow() + timedelta(seconds=30)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_HOME
    entity = hass.data[Platform.DEVICE_TRACKER].get_entity(entity_id)
    assert entity.is_connected is True
    assert entity.source_type == SourceType.ROUTER
    assert entity.battery_level == 100
    await async_test_rejoin(hass, zigpy_device_dt, [cluster], (2,))
    assert hass.states.get(entity_id).state == STATE_HOME