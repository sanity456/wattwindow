"""Read-only recheck of the exact source, ABI, wallets, and finalized flow."""
import base64
import hashlib
import json
from pathlib import Path

from release_support import rpc


ROOT = Path(__file__).resolve().parents[1]


def test_exact_submission_deployment_and_flow():
    manifest = json.loads((ROOT / "deployments" / "studionet.json").read_text(encoding="utf-8"))
    sources = list((ROOT / "contracts").glob("*.py"))
    assert len(sources) == 1
    source = sources[0].read_bytes()
    abi = json.loads((ROOT / "contracts" / "abi.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(source).hexdigest()
    address = manifest["contract_address"]
    assert rpc("eth_chainId", []) == "0xf22f"
    assert manifest["network"]["chain_id"] == 61999
    assert manifest["repository"] == ROOT.name
    assert manifest["source_sha256"] == source_hash == manifest["deployed_source_sha256"]
    assert manifest["full_flow_test"]["source_sha256"] == source_hash
    assert manifest["full_flow_test"]["status"] == "passed"
    assert manifest["source_bytes_match"] and manifest["deployed_abi_matches_local"]
    assert len({wallet.lower() for wallet in manifest["wallet_addresses"].values()}) == len(manifest["wallet_addresses"])
    assert base64.b64decode(rpc("gen_getContractCode", [address]), validate=True) == source
    assert rpc("gen_getContractSchema", [address]) == abi
    hashes = manifest["full_flow_test"]["transaction_hashes"]
    assert hashes["deploy"] == manifest["deployment_transaction_hash"]
    assert len(hashes) >= 2 and len(hashes) == len(set(hashes.values()))
    deployment = rpc("eth_getTransactionByHash", [hashes["deploy"]])
    assert deployment["to_address"].lower() == address.lower()
    assert base64.b64decode(deployment["data"]["contract_code"], validate=True) == source
    for label, transaction_hash in hashes.items():
        transaction = rpc("eth_getTransactionByHash", [transaction_hash])
        receipt = rpc("eth_getTransactionReceipt", [transaction_hash])
        assert transaction is not None and receipt is not None, label
        assert transaction["to_address"].lower() == address.lower(), label
        assert receipt["to"].lower() == address.lower(), label
        assert receipt["status"] == "0x1", label
