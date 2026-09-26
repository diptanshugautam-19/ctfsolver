---
challenge: mirror_pool
category: web
techniques: [read-only-reentrancy, flash-loan-pricing, virtual-price-manipulation, smart-contract-exploit]
time_to_flag: 8
status: solved
---

# MirrorLend (mirror_pool) — Solution Walkthrough

## Vulnerability Overview
The challenge features a lending platform (`MirrorLend`) that calculates maximum borrowable debt using the underlying liquidity pool's `get_virtual_price()`:
$$\text{maxDebt} = \frac{\text{collateralLP} \times \text{pool.get\_virtual\_price}()}{10^{18}}$$

In `Pool.sol`, `get_virtual_price()` is defined as:
$$\text{get\_virtual\_price}() = \frac{(\text{balance} + \text{token.balanceOf}(\text{this})) \times 10^{18}}{\text{totalSupply}}$$

However, in `Pool.removeLiquidity(lp)`:
```solidity
    function removeLiquidity(uint256 lp) external {
        uint256 ethOut = address(this).balance * lp / totalSupply;
        uint256 tokenOut = token.balanceOf(address(this)) * lp / totalSupply;
        balanceOf[msg.sender] -= lp;
        totalSupply -= lp;
        (bool ok, ) = msg.sender.call{value: ethOut}("");
        require(ok, "eth");
        require(token.transfer(msg.sender, tokenOut), "tok");
    }
```
`totalSupply` is immediately decreased by `lp`, and ETH is sent via `msg.sender.call{value: ethOut}("")` BEFORE `token.transfer(msg.sender, tokenOut)` is executed.

During the execution of `msg.sender.call`:
- `totalSupply` has shrunk.
- `token.balanceOf(address(this))` is STILL the full balance (not yet transferred).
- As a consequence, `get_virtual_price()` spikes dramatically during the reentrant callback!

## Exploitation Flow
1. Attacker transfers all 100 `mUSD` tokens from the player and deposits 10 ETH into `Pool.addLiquidity{value: 10 ether}(100 ether)`, receiving 110 LP tokens.
2. Attacker deposits a fraction (11 LP) into `MirrorLend` as collateral.
3. Attacker calls `Pool.removeLiquidity(99 ether)`.
4. Inside the `receive()` external callback:
   - `get_virtual_price()` is inflated from $\approx 1.0\times 10^{18}$ to $\approx 3.82\times 10^{18}$.
   - Attacker calls `MirrorLend.borrow(41.8 ether)` with the inflated collateral valuation.
   - `MirrorLend` records `totalDebt = 41.8 ether` and transfers tokens to the attacker.
5. The callback exits, `removeLiquidity` finishes, and `get_virtual_price()` normalizes back down to $1.0\times 10^{18}$.
6. `Setup.isSolved()` checks:
   $$\text{totalDebt} > \frac{\text{totalCollateralLP} \times \text{get\_virtual\_price}()}{10^{18}}$$
   $$41.8 > 11.0 \implies \mathbf{True}$$
7. The web server `/flag` endpoint validates `Setup.isSolved()` and returns the flag.

## Flag
`H7CTF{e2388a60-6b5c-4b62-87a2-a54e00341269}`
