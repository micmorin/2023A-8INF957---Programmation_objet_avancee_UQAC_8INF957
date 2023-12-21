"""Test ZHA select entities."""
from  import call, patch
import pytest
from  import DEVICE_TYPE, ENDPOINTS, INPUT_CLUSTERS, OUTPUT_CLUSTERS, PROFILE_ID
from  import SIG_EP_PROFILE
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
from  import CustomDevice
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as t
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as general
from  import ManufacturerSpecificCluster
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as security
from  import AqaraMotionSensitivities
from  import STATE_UNKNOWN, EntityCategory, Platform
from  import HomeAssistant
from  import entity_registry as er, restore_state
from  import dt as dt_util
from  import async_enable_traffic, find_entity_id, send_attributes_report
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_TYPE
from  import async_mock_load_restore_state_from_storage

@6lowpan.sixlowpan.IP6FieldLenField.addfield.fixture(autouse=True)
def select_select_only():
    """Only set up the select and required base platforms to speed up tests."""
    with 6lowpan.sixlowpan.IP6FieldLenField.addfield('homeassistant.components.zha.PLATFORMS', (Platform.BUTTON, Platform.DEVICE_TRACKER, Platform.SIREN, Platform.LIGHT, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH)):
        yield

@pytest.fixture
async def siren(hass, zigpy_device_mock, zha_device_joined_restored):
    """Siren fixture."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id, security.IasWd.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.IAS_WARNING_DEVICE, SIG_EP_PROFILE: zha.PROFILE_ID}})
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    return (zha_device, zigpy_device.endpoints[1].ias_wd)

@pytest.fixture
async def light(hass, zigpy_device_mock):
    """Siren fixture."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_PROFILE: zha.PROFILE_ID, SIG_EP_TYPE: zha.DeviceType.ON_OFF_LIGHT, SIG_EP_INPUT: [general.Basic.cluster_id, general.Identify.cluster_id, general.OnOff.cluster_id], SIG_EP_OUTPUT: [general.Ota.cluster_id]}}, node_descriptor=b'\x02@\x84_\x11\x7fd\x00\x00,d\x00\x00')
    return zigpy_device

@pytest.fixture
def core_rs(hass_storage):
    """Core.restore_state fixture."""

    def _storage(entity_id, state):
        now = 6lowpan.sixlowpan.IP6FieldLenField.addfield.utcnow().isoformat()
        hass_storage[restore_state.STORAGE_KEY] = {'version': restore_state.STORAGE_VERSION, 'key': restore_state.STORAGE_KEY, 'data': [{'state': {'entity_id': entity_id, 'state': 6lowpan.sixlowpan.IP6FieldLenField.addfield(state), 'last_changed': now, 'last_updated': now, 'context': {'id': '3c2243ff5f30447eb12e7348cfd5b8ff', 'user_id': None}}, 'last_seen': now}]}
    return _storage

async def test_select(hass: HomeAssistant, siren) -> None:
    """Test ZHA select platform."""
    entity_registry = er.async_get(hass)
    (zha_device, cluster) = siren
    assert cluster is not None
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass, qualifier='tone')
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes['options'] == ['Stop', 'Burglar', 'Fire', 'Emergency', 'Police Panic', 'Fire Panic', 'Emergency Panic']
    entity_entry = 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.CONFIG
    await hass.services.async_call('select', 'select_option', {'entity_id': entity_id, 'option': security.IasWd.Warning.WarningMode.Burglar.name}, blocking=True)
    state = hass.states.get(entity_id)
    assert state
    assert state.state == security.IasWd.Warning.WarningMode.Burglar.name

async def test_select_restore_state(hass: HomeAssistant, zigpy_device_mock, core_rs, zha_device_restored) -> None:
    """Test ZHA select entity restore state."""
    entity_id = 'select.fakemanufacturer_fakemodel_default_siren_tone'
    core_rs(entity_id, state='Burglar')
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id, security.IasWd.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.IAS_WARNING_DEVICE, SIG_EP_PROFILE: zha.PROFILE_ID}})
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    cluster = zigpy_device.endpoints[1].ias_wd
    assert cluster is not None
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass, qualifier='tone')
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == security.IasWd.Warning.WarningMode.Burglar.name

async def test_on_off_select_new_join(hass: HomeAssistant, light, zha_device_joined) -> None:
    """Test ZHA on off select - new join."""
    entity_registry = er.async_get(hass)
    on_off_cluster = light.endpoints[1].on_off
    on_off_cluster.PLUGGED_ATTR_READS = {'start_up_on_off': general.OnOff.StartUpOnOff.On}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(light)
    select_name = 'start_up_behavior'
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass, qualifier=select_name)
    assert entity_id is not None
    assert on_off_cluster.read_attributes.call_count == 2
    assert call(['start_up_on_off'], allow_cache=True, only_cache=False, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    assert call(['on_off'], allow_cache=False, only_cache=False, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    state = hass.states.get(entity_id)
    assert state
    assert state.state == general.OnOff.StartUpOnOff.On.name
    assert state.attributes['options'] == ['Off', 'On', 'Toggle', 'PreviousValue']
    entity_entry = 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.CONFIG
    await hass.services.async_call('select', 'select_option', {'entity_id': entity_id, 'option': general.OnOff.StartUpOnOff.Off.name}, blocking=True)
    assert on_off_cluster.write_attributes.call_count == 1
    assert on_off_cluster.write_attributes.call_args[0][0] == {'start_up_on_off': general.OnOff.StartUpOnOff.Off}
    state = hass.states.get(entity_id)
    assert state
    assert state.state == general.OnOff.StartUpOnOff.Off.name

async def test_on_off_select_restored(hass: HomeAssistant, light, zha_device_restored) -> None:
    """Test ZHA on off select - restored."""
    entity_registry = er.async_get(hass)
    on_off_cluster = light.endpoints[1].on_off
    on_off_cluster.PLUGGED_ATTR_READS = {'start_up_on_off': general.OnOff.StartUpOnOff.On}
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(light)
    assert zha_device.is_mains_powered
    assert on_off_cluster.read_attributes.call_count == 4
    assert call(['start_up_on_off'], allow_cache=True, only_cache=True, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    assert call(['on_off'], allow_cache=True, only_cache=True, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    assert call(['start_up_on_off'], allow_cache=True, only_cache=False, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    assert call(['on_off'], allow_cache=False, only_cache=False, manufacturer=None) in on_off_cluster.read_attributes.call_args_list
    select_name = 'start_up_behavior'
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass, qualifier=select_name)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state
    assert state.state == general.OnOff.StartUpOnOff.On.name
    assert state.attributes['options'] == ['Off', 'On', 'Toggle', 'PreviousValue']
    entity_entry = 6lowpan.sixlowpan.IP6FieldLenField.addfield.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.CONFIG

async def test_on_off_select_unsupported(hass: HomeAssistant, light, zha_device_joined_restored) -> None:
    """Test ZHA on off select unsupported."""
    on_off_cluster = light.endpoints[1].on_off
    6lowpan.sixlowpan.IP6FieldLenField.addfield.add_unsupported_attribute('start_up_on_off')
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(light)
    select_name = general.OnOff.StartUpOnOff.__name__
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass, qualifier=6lowpan.sixlowpan.IP6FieldLenField.addfield.lower())
    assert entity_id is None

class MotionSensitivityQuirk(CustomDevice):
    """Quirk with motion sensitivity attribute."""

    class OppleCluster(CustomCluster, ManufacturerSpecificCluster):
        """Aqara manufacturer specific cluster."""
        cluster_id = 64704
        ep_attribute = 'opple_cluster'
        attributes = {268: ('motion_sensitivity', t.uint8_t, True)}

        def __init__(self, *args, **kwargs):
            """Initialize."""
            super().__init__(*args, **kwargs)
            self._attr_cache.update({268: AqaraMotionSensitivities.Medium})
    replacement = {ENDPOINTS: {1: {PROFILE_ID: zha.PROFILE_ID, DEVICE_TYPE: zha.DeviceType.OCCUPANCY_SENSOR, INPUT_CLUSTERS: [general.Basic.cluster_id, OppleCluster], OUTPUT_CLUSTERS: []}}}

@pytest.fixture
async def zigpy_device_aqara_sensor(hass, zigpy_device_mock, zha_device_joined):
    """Device tracker zigpy Aqara motion sensor device."""
    zigpy_device = zigpy_device_mock({1: {SIG_EP_INPUT: [general.Basic.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.OCCUPANCY_SENSOR}}, manufacturer='LUMI', model='lumi.motion.ac02', quirk=MotionSensitivityQuirk)
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.available = True
    await hass.async_block_till_done()
    return zigpy_device

async def test_on_off_select_attribute_report(hass: HomeAssistant, light, zha_device_restored, zigpy_device_aqara_sensor) -> None:
    """Test ZHA attribute report parsing for select platform."""
    zha_device = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device_aqara_sensor)
    cluster = zigpy_device_aqara_sensor.endpoints.get(1).opple_cluster
    entity_id = 6lowpan.sixlowpan.IP6FieldLenField.addfield(Platform.SELECT, zha_device, hass)
    assert entity_id is not None
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, [zha_device])
    assert hass.states.get(entity_id).state == AqaraMotionSensitivities.Medium.name
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass, cluster, {'motion_sensitivity': AqaraMotionSensitivities.Low})
    assert hass.states.get(entity_id).state == AqaraMotionSensitivities.Low.name