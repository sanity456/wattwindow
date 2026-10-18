"""Opt-in full StudioNet flow; no wallet secret is stored in the repository."""
import hashlib
import json
import secrets

from gltest.types import TransactionHashVariant
from release_support import prepare, reject, save_negative_proof, save_proof, send


def test_studionet_wattwindow_flow():
    ctx = prepare("watt_window.py", ("owner", "operator", "witness"))
    contracts, accounts = ctx["contracts"], ctx["accounts"]
    transactions = {"deploy": ctx["deployment_hash"]}
    event_key = "release_" + secrets.token_hex(4)
    context = "Declared 18:00-19:00 local demand-response interval on 2026-10-12; baseline is 1000 Wh."
    send(transactions, "open_event", contracts["owner"].open_event(args=[event_key, context, accounts["operator"].address, accounts["witness"].address, 1000, 2000]))
    event_id = accounts["owner"].address.lower() + ":" + event_key
    opened = json.loads(contracts["owner"].get_event(args=[event_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert opened["status"] == "OPEN" and opened["baseline_wh"] == 1000
    report = "For the declared 18:00-19:00 local interval on 2026-10-12, the baseline was 1000 Wh and the actual reading was 700 Wh."
    witness_report = "I independently read 700 Wh actual against 1000 Wh baseline for the declared 18:00-19:00 local interval on 2026-10-12."
    salt = secrets.token_hex(16)
    payload = json.dumps({"event_id": event_id, "actual_wh": 700, "report": witness_report, "salt": salt},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    commitment = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    send(transactions, "commit_witness", contracts["witness"].commit_witness(args=[event_id, commitment]))
    send(transactions, "submit_reading", contracts["operator"].submit_reading(args=[event_id, 700, report]))
    send(transactions, "witness_reading", contracts["witness"].witness_reading(args=[event_id, 700, witness_report, salt]))
    final = json.loads(contracts["owner"].get_event(args=[event_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert final["status"] == "QUALIFIED" and final["assessment"] == "SUPPORTED" and final["reduction_bps"] == 3000, final

    save_proof(ctx, transactions, event_id, "QUALIFIED")


def test_studionet_wrong_reveal_guard():
    ctx = prepare("watt_window.py", ("owner", "operator", "witness"))
    contracts, accounts = ctx["contracts"], ctx["accounts"]
    transactions = {}
    # Live abuse-prevention demo: an incorrect witness reveal must fail and leave
    # the pending event byte-for-byte unchanged. This path avoids the LLM call.
    guard_key = "guard_" + secrets.token_hex(4)
    guard_context = "Declared 19:00-20:00 local interval; baseline is 1000 Wh."
    send(transactions, "open_guard_event", contracts["owner"].open_event(args=[guard_key, guard_context, accounts["operator"].address, accounts["witness"].address, 1000, 2000]))
    guard_id = accounts["owner"].address.lower() + ":" + guard_key
    guard_report = "For the declared 19:00-20:00 local interval, actual reading was 700 Wh against 1000 Wh baseline."
    guard_salt = secrets.token_hex(16)
    guard_payload = json.dumps({"event_id": guard_id, "actual_wh": 700, "report": guard_report, "salt": guard_salt},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    guard_commitment = hashlib.sha256(guard_payload.encode("utf-8")).hexdigest()
    send(transactions, "guard_commit_witness", contracts["witness"].commit_witness(args=[guard_id, guard_commitment]))
    send(transactions, "guard_submit_reading", contracts["operator"].submit_reading(args=[guard_id, 700, guard_report]))
    before_rejection = json.loads(contracts["owner"].get_event(args=[guard_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    wrong_salt = "0" * 32 if guard_salt != "0" * 32 else "1" * 32
    rejected = reject(transactions, "reject_wrong_witness_reveal", contracts["witness"].witness_reading(args=[guard_id, 700, guard_report, wrong_salt]))
    after_rejection = json.loads(contracts["owner"].get_event(args=[guard_id]).call(transaction_hash_variant=TransactionHashVariant.LATEST_FINAL))
    assert after_rejection == before_rejection and after_rejection["status"] == "AWAITING_WITNESS", after_rejection
    negative_tests = {"wrong_witness_reveal": {**rejected, "event_id": guard_id,
        "expected_state_after": "AWAITING_WITNESS", "state_unchanged": True, "state_after": after_rejection}}
    save_negative_proof(transactions, "wrong_witness_reveal", negative_tests["wrong_witness_reveal"])
