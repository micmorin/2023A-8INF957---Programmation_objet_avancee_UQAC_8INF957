"""Test ZHA base cluster handlers module."""
from  import parse_and_log_command
from  import endpoint, poll_control_ch, zigpy_coordinator_device

def test_parse_and_log_command(poll_control_ch):
    """Test that `parse_and_log_command` correctly parses a known command."""
    assert parse_and_log_command(poll_control_ch, 0, 1, []) == 'fast_poll_stop'

def test_parse_and_log_command_unknown(poll_control_ch):
    """Test that `parse_and_log_command` correctly parses an unknown command."""
    assert parse_and_log_command(poll_control_ch, 0, 171, []) == '0xAB'