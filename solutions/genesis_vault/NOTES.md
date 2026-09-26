---
challenge: genesis_vault
category: web3
techniques: [erc4626-inflation-attack, share-rounding-to-zero, donation-sync-manipulation]
time_to_flag: 10
status: verified_local
---

# Genesis Vault — Solution & Vulnerability Analysis

## 1. Vulnerability Summary
The challenge implements a classic ERC-4626 style vault (`GenesisVault.sol`) susceptible to the **First Depositor / Share Inflation Attack**:
1. When `totalSupply == 0`, the vault converts assets 1:1 to shares.
2. In subsequent deposits, share calculation rounds down:
   $$\text{shares} = \frac{\text{assets} \times \text{totalSupply}}{\text{reserve}}$$
3. The vault features a `sync()` method:
   $$\text{reserve} = \text{asset.balanceOf}(\text{address}(\text{this}))$$
   which allows any direct token donation to update the internal `reserve` without minting any new shares (`totalSupply` remains unchanged).

## 2. Attack Mechanics
- **Initial Setup:**
  - Player starts with $200\text{ ether}$ of `Token`.
  - Setup contract holds $100\text{ ether}$ of `Token` designated for `victimDeposit()`.
  - Success condition: `victimDeposited && vault.balanceOf(victim) == 0 && token.balanceOf(vault) < 1 ether`.

- **Exploit Steps:**
  1. **Deposit 1 wei:**
     - Player deposits $1\text{ wei}$ of `Token` when `totalSupply == 0`.
     - Vault mints $1\text{ share}$ to Player.
     - `reserve = 1`, `totalSupply = 1`.
  2. **Direct Donation + Sync:**
     - Player transfers $100\text{ ether}$ directly to `address(vault)`.
     - Player calls `vault.sync()`.
     - `reserve` becomes $100\text{ ether} + 1\text{ wei}$, while `totalSupply` remains $1$.
  3. **Victim Deposit (Anchor Investor):**
     - `Setup.victimDeposit()` deposits $100\text{ ether}$.
     - Share calculation:
       $$\text{shares} = \frac{100\text{ ether} \times 1}{100\text{ ether} + 1} = 0$$
     - Due to integer division rounding down to zero, the anchor investor receives $0\text{ shares}$ (`balanceOf[victim] == 0`)!
     - `reserve` increases to $200\text{ ether} + 1\text{ wei}$, `totalSupply` remains $1$.
  4. **Redeem Shares:**
     - Player redeems their $1\text{ share}$:
       $$\text{assets} = \frac{1 \times (200\text{ ether} + 1)}{1} = 200\text{ ether} + 1$$
     - Vault pays out the entire reserve to the Player.
     - `vault.balanceOf(victim) == 0`, `token.balanceOf(vault) == 0`.
     - Player finishes with $300\text{ ether}$ of `Token`.
  5. `Setup.isSolved()` evaluates to `True`.

## 3. Exploit Implementation
The attack is implemented both as a standalone atomic Solidity contract (`Exploit.sol`) and an automated Web3 solver (`solve.py` / `test_local.py`).
