"""Test zha siren."""
from  import timedelta
from  import ANY, call, patch
import pytest
from  import SIG_EP_PROFILE
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
import 6lowpan.sixlowpan.IP6FieldLenField.addfield
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as security
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import ATTR_DURATION, ATTR_TONE, ATTR_VOLUME_LEVEL, DOMAIN as SIREN_DOMAIN
from  import WARNING_DEVICE_MODE_EMERGENCY_PANIC, WARNING_DEVICE_SOUND_MEDIUM
from  import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, Platform
from  import HomeAssistant
import homeassistant.util.dt as dt_util
from  import async_enable_traffic, find_entity_id
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_TYPE
from  import async_fire_time_changed

@pytest.fixture(autouse=True)
def siren_platform_only():
    """Only set up the siren and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.DEVICE_TRACKER, Platform.NUMBER, Platform.SENSOR, Platform.SELECT, Platform.SIREN)):
        yield

@pytest.fixture
async def siren(hass, zigpy_device_mock, zha_device_joined_restored):
    """Siren fixture."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id, security.IasWd.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.IAS_WARNING_DEVICE, SIG_EP_PROFILE: zha.PROFILE_ID}})
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    return (zha_device, zigpy_device.endpoints[1].ias_wd)

async def test_siren(hass: HomeAssistant, siren) -> None:
    """Test zha siren platform."""
    (zha_device, cluster) = siren
    assert cluster is not None
    entity_id = find_entity_id(Platform.SIREN, zha_device, hass)
    assert entity_id is not None
    assert hass.states.get(entity_id).state == STATE_OFF
    await async_enable_traffic(hass, [zha_device], enabled=False)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    await async_enable_traffic(hass, [zha_device])
    assert hass.states.get(entity_id).state == STATE_OFF
    with patch('zigpy.device.Device.request', return_value=[0, zcl_f.Status.SUCCESS]), patch('zigpy.zcl.Cluster.request', side_effect=zigpy.zcl.Cluster.request, autospec=True):
        await hass.services.async_call(SIREN_DOMAIN, 'turn_on', {'entity_id': entity_id}, blocking=True)
        assert cluster.request.mock_calls == [call(cluster, False, 0, ANY, 50, 5, 0, 2, manufacturer=None, expect_reply=True, tsn=None)]
    assert hass.states.get(entity_id).state == STATE_ON
    with patch('zigpy.device.Device.request', return_value=[1, zcl_f.Status.SUCCESS]), patch('zigpy.zcl.Cluster.request', side_effect=zigpy.zcl.Cluster.request, autospec=True):
        await hass.services.async_call(SIREN_DOMAIN, 'turn_off', {'entity_id': entity_id}, blocking=True)
        assert cluster.request.mock_calls == [call(cluster, False, 0, ANY, 2, 5, 0, 2, manufacturer=None, expect_reply=True, tsn=None)]
    assert hass.states.get(entity_id).state == STATE_OFF
    with patch('zigpy.device.Device.request', return_value=[0, zcl_f.Status.SUCCESS]), patch('zigpy.zcl.Cluster.request', side_effect=zigpy.zcl.Cluster.request, autospec=True):
        await hass.services.async_call(SIREN_DOMAIN, 'turn_on', {'entity_id': entity_id, ATTR_DURATION: 10, ATTR_TONE: WARNING_DEVICE_MODE_EMERGENCY_PANIC, ATTR_VOLUME_LEVEL: WARNING_DEVICE_SOUND_MEDIUM}, blocking=True)
        assert cluster.request.mock_calls == [call(cluster, False, 0, ANY, 97, 10, 0, 2, manufacturer=None, expect_reply=True, tsn=None)]
    assert hass.states.get(entity_id).state == STATE_ON
    now = dt_util.utcnow() + timedelta(seconds=15)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_OFF