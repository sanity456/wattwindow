import hashlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def setup(direct_vm, direct_deploy, direct_accounts):
    owner, operator, witness, outsider = direct_accounts[:4]
    direct_vm.sender = owner
    source = Path(__file__).parents[1] / "contracts" / "watt_window.py"
    contract = direct_deploy(str(source), sdk_version="v0.2.16")
    event_id = contract.open_event("weekday_peak", "Window 18:00-19:00 local on 2026-10-12; baseline 1000 Wh.", operator, witness, 1000, 2000)
    return contract, event_id, owner, operator, witness, outsider


def mock(vm, assessment):
    vm.clear_mocks()
    vm.mock_llm("Reconcile two separately wallet-attested demand-response reports", json.dumps({"assessment": assessment}))


SALT = "0123456789abcdef0123456789abcdef"


def commit(vm, contract, witness, event_id, actual_wh, report):
    payload = json.dumps({"event_id": event_id, "actual_wh": actual_wh, "report": report, "salt": SALT},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    vm.sender = witness
    contract.commit_witness(event_id, hashlib.sha256(payload.encode("utf-8")).hexdigest())


def test_qualifies_only_with_supported_report_and_threshold(setup, direct_vm):
    contract, event_id, _owner, operator, witness, _outsider = setup
    witness_report = "I separately read 700 Wh for the same 18:00-19:00 local on 2026-10-12 interval; baseline was 1000 Wh."
    commit(direct_vm, contract, witness, event_id, 700, witness_report)
    direct_vm.sender = operator
    assert contract.submit_reading(event_id, 700, "For window 18:00-19:00 local on 2026-10-12, baseline was 1000 Wh and actual was 700 Wh.") == "AWAITING_WITNESS"
    direct_vm.sender = witness
    mock(direct_vm, "SUPPORTED")
    assert contract.witness_reading(event_id, 700, witness_report, SALT) == "QUALIFIED"
    state = json.loads(contract.get_event(event_id))
    assert state["reduction_bps"] == 3000 and state["status"] == "QUALIFIED"
    with direct_vm.expect_revert("pending event witness only"):
        contract.witness_reading(event_id, 700, "Repeated reading", SALT)
    assert direct_vm.run_validator(leader_result="SUPPORTED")
    assert not direct_vm.run_validator(leader_result="CONTRADICTED")


def test_uncertain_and_shortfall_are_not_qualified(setup, direct_vm):
    contract, event_id, owner, operator, witness, _outsider = setup
    commit(direct_vm, contract, witness, event_id, 700, "I am not sure.")
    direct_vm.sender = operator
    assert contract.submit_reading(event_id, 700, "A change occurred, maybe.") == "AWAITING_WITNESS"
    direct_vm.sender = witness
    mock(direct_vm, "UNCERTAIN")
    assert contract.witness_reading(event_id, 700, "I am not sure.", SALT) == "UNRESOLVED"
    direct_vm.sender = owner
    second = contract.open_event("second", "A separate 18:00-19:00 event.", operator, witness, 1000, 2000)
    second_report = "I saw 900 Wh actual against 1000 Wh baseline in the separate 18:00-19:00 event."
    commit(direct_vm, contract, witness, second, 900, second_report)
    direct_vm.sender = operator
    contract.submit_reading(second, 900, "For the separate 18:00-19:00 event, baseline 1000 Wh and actual 900 Wh.")
    direct_vm.sender = witness
    mock(direct_vm, "SUPPORTED")
    assert contract.witness_reading(second, 900, second_report, SALT) == "NOT_QUALIFIED"
    assert json.loads(contract.get_event(second))["reduction_bps"] == 1000
    direct_vm.sender = owner
    third = contract.open_event("third", "A third event.", operator, witness, 1000, 2000)
    commit(direct_vm, contract, witness, third, 800, "Actual 800 Wh.")
    direct_vm.sender = operator
    contract.submit_reading(third, 700, "Actual 700 Wh.")
    direct_vm.sender = witness
    assert contract.witness_reading(third, 800, "Actual 800 Wh.", SALT) == "DISPUTED"


def test_roles_bad_input_and_model_failure_leave_state_unchanged(setup, direct_vm, direct_accounts):
    contract, event_id, owner, operator, witness, outsider = setup
    direct_vm.sender = outsider
    with direct_vm.expect_revert("operator only"):
        contract.submit_reading(event_id, 700, "Something")
    direct_vm.sender = owner
    with direct_vm.expect_revert("three distinct nonzero roles"):
        contract.open_event("bad", "Context", owner, witness, 1000, 2000)
    with direct_vm.expect_revert("baseline out of range"):
        contract.open_event("bad", "Context", operator, witness, 0, 2000)
    direct_vm.sender = operator
    with direct_vm.expect_revert("committed event operator only"):
        contract.submit_reading(event_id, 700, "An operator report")
    commit(direct_vm, contract, witness, event_id, 700, "A witness report")
    direct_vm.sender = operator
    contract.submit_reading(event_id, 700, "An operator report")
    direct_vm.sender = witness
    before = contract.get_event(event_id)
    with direct_vm.expect_revert("reveal does not match"):
        contract.witness_reading(event_id, 700, "A witness report", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    mock(direct_vm, "WRONG")
    with direct_vm.expect_revert("invalid assessment"):
        contract.witness_reading(event_id, 700, "A witness report", SALT)
    assert contract.get_event(event_id) == before
    direct_vm.sender = outsider
    other = contract.open_event("weekday_peak", "Another owner's event.", operator, witness, 1000, 2000)
    assert other != event_id
