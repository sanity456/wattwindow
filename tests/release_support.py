"""Isolated wallet and exact StudioNet source checks for the release test."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

from eth_account import Account
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address
import requests


ROOT = Path(__file__).resolve().parents[1]
RPC = "https://studio.genlayer.com/api"


def rpc(method, params):
    error = None
    for attempt in range(8):
        try:
            response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=(10, 30))
            if response.status_code not in (429, 500, 502, 503, 504):
                response.raise_for_status()
                body = response.json()
                if body.get("error"):
                    raise AssertionError(json.dumps(body["error"], sort_keys=True))
                return body["result"]
            error = RuntimeError(f"StudioNet HTTP {response.status_code}")
        except (requests.RequestException, ValueError) as caught:
            error = caught
        if attempt < 7:
            time.sleep(min(2 + attempt * 2, 12))
    raise AssertionError(f"StudioNet RPC failed: {error}")


def receipt_hash(receipt):
    value = receipt.get("hash") or receipt.get("tx_id") or receipt.get("tx_hash") or receipt.get("transactionHash")
    assert isinstance(value, str) and value.startswith("0x"), json.dumps(receipt, default=str)
    return value


def prepare(source_name, roles):
    import win32crypt
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA required for DPAPI wallet isolation")
    folder = Path(local) / "GenLayerStudioNetBatchBC-v3-20261012" / ROOT.name
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"{role}.dpapi" for role in roles]
    if any(path.exists() for path in paths) and not all(path.exists() for path in paths):
        raise RuntimeError("Partial wallet store; inspect before continuing")
    accounts = {}
    for role, path in zip(roles, paths):
        if path.exists():
            raw = win32crypt.CryptUnprotectData(path.read_bytes(), None, None, None, 0)[1]
            accounts[role] = Account.from_key(raw)
        else:
            account = Account.create()
            path.write_bytes(win32crypt.CryptProtectData(bytes(account.key), f"GenLayer {ROOT.name} StudioNet", None, None, None, 0))
            accounts[role] = account
    if len({account.address.lower() for account in accounts.values()}) != len(accounts):
        raise RuntimeError("Wallet collision")
    source_path = ROOT / "contracts" / source_name
    source = source_path.read_bytes()
    source_sha256 = hashlib.sha256(source).hexdigest()
    abi = json.loads((ROOT / "contracts" / "abi.json").read_text(encoding="utf-8"))
    factory = get_contract_factory(contract_file_path=source_path)
    progress_path = folder / "deployment-progress.json"
    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        assert progress["source_sha256"] == source_sha256
        assert progress["wallet_addresses"] == {name: item.address for name, item in accounts.items()}
        address, deployment_hash = progress["contract_address"], progress["deployment_transaction_hash"]
    else:
        deployed = factory.deploy_contract_tx(args=[], account=accounts[roles[0]], wait_transaction_status=TransactionStatus.FINALIZED, wait_interval=10000, wait_retries=300)
        assert tx_execution_succeeded(deployed), json.dumps(deployed, default=str)
        address, deployment_hash = extract_contract_address(deployed), receipt_hash(deployed)
        progress_path.write_text(json.dumps({"source_sha256": source_sha256, "wallet_addresses": {name: item.address for name, item in accounts.items()}, "contract_address": address, "deployment_transaction_hash": deployment_hash}, indent=2) + "\n", encoding="utf-8")
    assert rpc("eth_chainId", []) == "0xf22f"
    deployed_source = base64.b64decode(rpc("gen_getContractCode", [address]), validate=True)
    assert deployed_source == source, "Deployed source is stale"
    assert rpc("gen_getContractSchema", [address]) == abi, "Deployed ABI differs from local"
    contracts = {role: factory.build_contract(address, account=accounts[role]) for role in roles}
    return {"factory": factory, "accounts": accounts, "contracts": contracts, "address": address, "deployment_hash": deployment_hash, "source_sha256": source_sha256, "abi": abi}


def send(transactions, label, call):
    receipt = call.transact(wait_transaction_status=TransactionStatus.FINALIZED, wait_interval=10000, wait_retries=300)
    assert tx_execution_succeeded(receipt), json.dumps(receipt, default=str)
    transactions[label] = receipt_hash(receipt)


def save_proof(ctx, transactions, flow_id, final_state):
    (ROOT / "deployments").mkdir(parents=True, exist_ok=True)
    record = {"schema": "genlayer-submission-evidence/v2", "network": {"name": "studionet", "chain_id": 61999, "rpc": RPC}, "repository": ROOT.name,
        "contract_address": ctx["address"], "deployment_transaction_hash": ctx["deployment_hash"],
        "wallet_addresses": {role: account.address for role, account in ctx["accounts"].items()},
        "source_sha256": ctx["source_sha256"], "deployed_source_sha256": ctx["source_sha256"], "source_bytes_match": True,
        "deployed_abi_matches_local": True,
        "abi_sha256": hashlib.sha256(json.dumps(ctx["abi"], sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "full_flow_test": {"status": "passed", "workflow_id": flow_id, "final_state": final_state,
            "transaction_hashes": transactions, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "test_file": "tests/studionet_smoke.py", "source_sha256": ctx["source_sha256"]}}
    (ROOT / "deployments" / "studionet.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"contract_address": ctx["address"], "final_state": final_state, "wallet_addresses": record["wallet_addresses"]}, sort_keys=True))
