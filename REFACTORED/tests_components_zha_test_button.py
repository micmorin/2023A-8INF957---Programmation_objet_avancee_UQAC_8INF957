"""Test ZHA button."""
from  import call, patch
from  import freeze_time
import pytest
from  import DEVICE_TYPE, ENDPOINTS, INPUT_CLUSTERS, OUTPUT_CLUSTERS, PROFILE_ID
from  import ParksideTuyaValveManufCluster
from  import SIG_EP_PROFILE
from  import ZigbeeException
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
from  import CustomDevice
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as t
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
from  import ManufacturerSpecificCluster
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as security
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zcl_f
from  import DOMAIN, SERVICE_PRESS, ButtonDeviceClass
from  import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, STATE_UNKNOWN, EntityCategory, Platform
from  import HomeAssistant
from  import HomeAssistantError
from  import entity_registry as er
from  import find_entity_id
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_TYPE

@6lowpan.sixlowpan.IP6FieldLenField.addfield.fixture(autouse=True)
def button_platform_only():
    """Only set up the button and required base platforms to speed up tests."""
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('homeassistant.components.zha.PLATFORMS', (Platform.BINARY_SENSOR, Platform.BUTTON, Platform.DEVICE_TRACKER, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH)):
        yield

@pytest.fixture
async def contact_sensor(hass, zigpy_device_mock, zha_device_joined_restored):
    """Contact sensor fixture."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id, general.Identify.cluster_id, security.IasZone.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.IAS_ZONE, SIG_EP_PROFILE: zha.PROFILE_ID}})
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    return (zha_device, zigpy_device.endpoints[1].identify)

class FrostLockQuirk(CustomDevice):
    """Quirk with frost lock attribute."""

    class TuyaManufCluster(CustomCluster, ManufacturerSpecificCluster):
        """Tuya manufacturer specific cluster."""
        cluster_id = 61184
        ep_attribute = 'tuya_manufacturer'
        attributes = {61185: ('frost_lock_reset', t.Bool)}
    replacement = {ENDPOINTS: {1: {PROFILE_ID: zha.PROFILE_ID, DEVICE_TYPE: zha.DeviceType.ON_OFF_SWITCH, INPUT_CLUSTERS: [general.Basic.cluster_id, TuyaManufCluster], OUTPUT_CLUSTERS: []}}}

@pytest.fixture
async def tuya_water_valve(hass, zigpy_device_mock, zha_device_joined_restored):
    """Tuya Water Valve fixture."""
    zigpy_device = zigpy_device_mock({1: {PROFILE_ID: zha.PROFILE_ID, DEVICE_TYPE: zha.DeviceType.ON_OFF_SWITCH, INPUT_CLUSTERS: [general.Basic.cluster_id, general.Identify.cluster_id, general.Groups.cluster_id, general.Scenes.cluster_id, general.OnOff.cluster_id, ParksideTuyaValveManufCluster.cluster_id], OUTPUT_CLUSTERS: [general.Time.cluster_id, general.Ota.cluster_id]}}, manufacturer='_TZE200_htnnfasr', model='TS0601')
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    return (zha_device, zigpy_device.endpoints[1].tuya_manufacturer)

@6lowpan.sixlowpan.IP6FieldLenField.addfield('2021-11-04 17:37:00', tz_offset=-1)
async def test_button(hass: HomeAssistant, contact_sensor) -> None:
    """Test ZHA button platform."""
    entity_registry = er.async_get(hass)
    (zha_device, cluster) = contact_sensor
    assert cluster is not None
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(DOMAIN, zha_device, hass)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_DEVICE_CLASS] == ButtonDeviceClass.IDENTIFY
    entry = 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_get(entity_id)
    assert entry
    assert entry.entity_category == EntityCategory.DIAGNOSTIC
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True)
        await hass.async_block_till_done()
        assert len(cluster.request.mock_calls) == 1
        assert cluster.request.call_args[0][0] is False
        assert cluster.request.call_args[0][1] == 0
        assert cluster.request.call_args[0][3] == 5
    state = hass.states.get(entity_id)
    assert state
    assert state.state == '2021-11-04T16:37:00+00:00'
    assert state.attributes[ATTR_DEVICE_CLASS] == ButtonDeviceClass.IDENTIFY

async def test_frost_unlock(hass: HomeAssistant, tuya_water_valve) -> None:
    """Test custom frost unlock ZHA button."""
    entity_registry = er.async_get(hass)
    (zha_device, cluster) = tuya_water_valve
    assert cluster is not None
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(DOMAIN, zha_device, hass, qualifier='frost_lock_reset')
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_DEVICE_CLASS] == ButtonDeviceClass.RESTART
    entry = 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_get(entity_id)
    assert entry
    assert entry.entity_category == EntityCategory.CONFIG
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('zigpy.zcl.Cluster.request', return_value=[0, zcl_f.Status.SUCCESS]):
        await hass.services.async_call(DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True)
        await hass.async_block_till_done()
        assert cluster.write_attributes.mock_calls == [call({'frost_lock_reset': 0}, manufacturer=None)]
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_DEVICE_CLASS] == ButtonDeviceClass.RESTART
    cluster.write_attributes.reset_mock()
    cluster.write_attributes.side_effect = ZigbeeException
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True)
    assert cluster.write_attributes.mock_calls == [call({'frost_lock_reset': 0}, manufacturer=None), call({'frost_lock_reset': 0}, manufacturer=None), call({'frost_lock_reset': 0}, manufacturer=None)]