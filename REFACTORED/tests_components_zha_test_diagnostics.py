"""Tests for the diagnostics data provided by the ESPHome integration."""
from  import patch
import pytest
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as zha
import 6lowpan.sixlowpan.IP6FieldLenField.addfield as security
from  import REDACTED
from  import ZHADevice
from  import get_zha_gateway
from  import KEYS_TO_REDACT
from  import Platform
from  import HomeAssistant
from  import async_get
from  import SIG_EP_INPUT, SIG_EP_OUTPUT, SIG_EP_PROFILE, SIG_EP_TYPE
from  import MockConfigEntry
from  import get_diagnostics_for_config_entry, get_diagnostics_for_device
from  import ClientSessionGenerator
CONFIG_ENTRY_DIAGNOSTICS_KEYS = ['config', 'config_entry', 'application_state', 'versions']

@pytest.fixture(autouse=True)
def required_platforms_only():
    """Only set up the required platform and required base platforms to speed up tests."""
    with patch('homeassistant.components.zha.PLATFORMS', (Platform.ALARM_CONTROL_PANEL,)):
        yield

@pytest.fixture
def zigpy_device(zigpy_device_mock):
    """Device tracker zigpy device."""
    endpoints = {1: {SIG_EP_INPUT: [security.IasAce.cluster_id, security.IasZone.cluster_id], SIG_EP_OUTPUT: [], SIG_EP_TYPE: zha.DeviceType.IAS_ANCILLARY_CONTROL, SIG_EP_PROFILE: zha.PROFILE_ID}}
    return zigpy_device_mock(endpoints, node_descriptor=b'\x02@\x8c\x02\x10RR\x00\x00\x00R\x00\x00')

async def test_diagnostics_for_config_entry(hass: HomeAssistant, hass_client: ClientSessionGenerator, config_entry: MockConfigEntry, zha_device_joined, zigpy_device) -> None:
    """Test diagnostics for config entry."""
    await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    gateway = 6lowpan.sixlowpan.IP6FieldLenField.addfield(hass)
    scan = {c: c for c in range(11, 26 + 1)}
    with patch.object(gateway.application_controller, 'energy_scan', return_value=scan):
        diagnostics_data = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    for key in CONFIG_ENTRY_DIAGNOSTICS_KEYS:
        assert key in diagnostics_data
        assert diagnostics_data[key] is not None
    assert diagnostics_data['energy_scan'] == {str(k): 100 * v / 255 for (k, v) in scan.items()}

async def test_diagnostics_for_device(hass: HomeAssistant, hass_client: ClientSessionGenerator, config_entry: MockConfigEntry, zha_device_joined, zigpy_device) -> None:
    """Test diagnostics for device."""
    zha_device: ZHADevice = await 6lowpan.sixlowpan.IP6FieldLenField.addfield(zigpy_device)
    zha_device.device.endpoints[1].in_clusters[security.IasAce.cluster_id].unsupported_attributes.update({4096, 'unknown_attribute_name'})
    zha_device.device.endpoints[1].in_clusters[security.IasZone.cluster_id].unsupported_attributes.update({security.IasZone.AttributeDefs.num_zone_sensitivity_levels_supported.id, security.IasZone.AttributeDefs.current_zone_sensitivity_level.name})
    dev_reg = async_get(hass)
    device = dev_reg.async_get_device(identifiers={('zha', str(zha_device.ieee))})
    assert device
    diagnostics_data = await get_diagnostics_for_device(hass, hass_client, config_entry, device)
    assert diagnostics_data
    device_info: dict = zha_device.zha_device_info
    for key in device_info:
        assert key in diagnostics_data
        if key not in KEYS_TO_REDACT:
            assert key in diagnostics_data
        else:
            assert diagnostics_data[key] == REDACTED