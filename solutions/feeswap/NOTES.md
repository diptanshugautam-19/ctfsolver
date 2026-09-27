---
challenge: feeswap
category: web3
techniques: [solana-token-2022, amm-reserve-drain, transfer-checked, interactive-solana-launcher]
time_to_flag: 15
status: solved
---

# feeswap

## Challenge Description
> feeswap is a tiny two-asset pool: send it token A, get token B back. a clean 1:1 desk with a healthy B reserve it's sure it can always cover.
> you're holding token A. walk out with the pool's entire B reserve.
> nc web3.h7tex.com 42583

## Analysis
The challenge consists of a custom Solana program `fee_swap` written using `spl-token-2022` and Borsh serialization.

The program exposes:
- `Ix::InitPool`: Initializes pool state with `vault_a`, `vault_b`, `mint_a`, and `mint_b`.
- `Ix::SwapAToB { amount }`: Swaps Token A to Token B.
- `Ix::SwapBToA { amount }`: Swaps Token B to Token A.

### Key Mechanism & Flaw
1. The swap formula computes:
   `payout = amount - (amount * SWAP_FEE_BPS / 10_000)` where `SWAP_FEE_BPS = 100` (1% fee).
2. The user holds 100 Token A (`100_000_000` base units with 6 decimals).
3. The pool holds 100 Token B (`100_000_000` base units) in `vault_b`.
4. The challenge launcher checks whether `vault_b` has been drained to `<= 1_000_000` (threshold reserve coverage).
5. Calling `Ix::SwapAToB` with `amount = 100_000_000`:
   - `in_ix` transfers 100 Token A from `user_a` to `vault_a`.
   - `payout = 100_000_000 - 1_000_000 = 99_000_000` Token B transferred to `user_b`.
   - `vault_b remaining: 1_000_000`.
   - Win condition triggers: `reserve drained.`

## Flag
`H7CTF{ba72db0b-6a04-413a-9600-0c5f989ccb35}`
