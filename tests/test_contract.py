import json
from pathlib import Path

import pytest


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_accounts):
    owner, operator, outsider = direct_accounts[:3]
    direct_vm.sender = owner
    source = Path(__file__).parents[1] / "contracts" / "watt_window.py"
    contract = direct_deploy(str(source), sdk_version="v0.2.16")
    event_id = contract.open_event("weekday_peak", "Window 18:00-19:00 local on 2026-10-12; baseline 1000 Wh.", operator, 1000, 2000)
    return contract, event_id, owner, operator, outsider


def mock(vm, assessment):
    vm.clear_mocks()
    vm.mock_llm("Review one public demand-response report", json.dumps({"assessment": assessment}))


def test_qualifies_only_with_supported_report_and_threshold(setup, direct_vm):
    contract, event_id, _owner, operator, _outsider = setup
    direct_vm.sender = operator
    mock(direct_vm, "SUPPORTED")
    assert contract.submit_reading(event_id, 700, "For window 18:00-19:00 local on 2026-10-12, baseline was 1000 Wh and actual was 700 Wh.") == "QUALIFIED"
    state = json.loads(contract.get_event(event_id))
    assert state["reduction_bps"] == 3000 and state["status"] == "QUALIFIED"
    with direct_vm.expect_revert("open event operator only"):
        contract.submit_reading(event_id, 700, "Repeated reading")
    assert direct_vm.run_validator(leader_result="SUPPORTED")
    assert not direct_vm.run_validator(leader_result="CONTRADICTED")


def test_uncertain_and_shortfall_are_not_qualified(setup, direct_vm):
    contract, event_id, owner, operator, _outsider = setup
    direct_vm.sender = operator
    mock(direct_vm, "UNCERTAIN")
    assert contract.submit_reading(event_id, 700, "A change occurred, maybe.") == "UNRESOLVED"
    direct_vm.sender = owner
    second = contract.open_event("second", "A separate 18:00-19:00 event.", operator, 1000, 2000)
    direct_vm.sender = operator
    mock(direct_vm, "SUPPORTED")
    assert contract.submit_reading(second, 900, "For the separate 18:00-19:00 event, baseline 1000 Wh and actual 900 Wh.") == "NOT_QUALIFIED"
    assert json.loads(contract.get_event(second))["reduction_bps"] == 1000


def test_roles_bad_input_and_model_failure_leave_state_unchanged(setup, direct_vm, direct_accounts):
    contract, event_id, owner, operator, outsider = setup
    direct_vm.sender = outsider
    with direct_vm.expect_revert("operator only"):
        contract.submit_reading(event_id, 700, "Something")
    direct_vm.sender = owner
    with direct_vm.expect_revert("distinct nonzero operator"):
        contract.open_event("bad", "Context", owner, 1000, 2000)
    with direct_vm.expect_revert("baseline out of range"):
        contract.open_event("bad", "Context", operator, 0, 2000)
    direct_vm.sender = operator
    before = contract.get_event(event_id)
    mock(direct_vm, "WRONG")
    with direct_vm.expect_revert("invalid assessment"):
        contract.submit_reading(event_id, 700, "A report")
    assert contract.get_event(event_id) == before
    direct_vm.sender = direct_accounts[3]
    other = contract.open_event("weekday_peak", "Another owner's event.", operator, 1000, 2000)
    assert other != event_id
