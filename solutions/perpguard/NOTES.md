---
challenge: perpguard
category: web3
techniques: [solana-compute-budget-exhaustion, liquidation-dos, open-many-padding, sbf-cpi-proxy]
time_to_flag: 20
status: solved
---

# perpguard

## Challenge Description
> perpguard is a solana lending market: post collateral, open positions, borrow.
> you're a borrower who plans to default, and your collateral is about to be marked down. end up underwater on a loan no keeper can ever claw back. nc web3.h7tex.com 43215

## Analysis
The challenge features a Solana lending market program (`perp_guard`) implemented in Rust using Borsh serialization and custom account layouts.

The program exposes instructions:
- `Ix::InitMarket`
- `Ix::SetPrice`
- `Ix::InitObligation`
- `Ix::OpenPosition`
- `Ix::Liquidate`
- `Ix::OpenMany { collateral, debt, count }`

### Vulnerability: Unbounded Loop in Liquidation (Denial of Service)
In `Ix::Liquidate`:
```rust
let count = rd_u64(&data, COUNT_OFF) as usize;
let mut allowed_debt: u128 = 0;
let mut total_debt: u128 = 0;
for i in 0..count {
    let off = HEADER + i * POS_SIZE;
    let value = (rd_u64(&data, off) as u128).saturating_mul(price) / PRICE_SCALE;
    allowed_debt = allowed_debt.saturating_add(value.saturating_mul(LTV_NUM) / LTV_DEN);
    total_debt = total_debt.saturating_add(rd_u64(&data, off + 8) as u128);
}
if total_debt <= allowed_debt {
    return Err(ProgramError::InvalidArgument);
}
data[SEIZED_OFF] = 1;
```

1. To liquidate an unhealthy obligation, the keeper must execute `Ix::Liquidate`, which loops over all `count` positions in the account to calculate total collateral value and debt.
2. In Solana, transactions are strictly constrained by the Compute Unit (CU) budget (default 200,000 CU).
3. `Ix::OpenMany` allows the borrower to append multiple positions in a single transaction as long as `healthy(collateral, debt, price)` holds.
4. Setting `collateral = 0, debt = 0` satisfies `healthy()` (`0 <= 0`), allowing up to 10,000 zero-value positions to be appended to the obligation in one call.
5. With `count = 10001`, the keeper's `Ix::Liquidate` transaction runs out of compute units and fails (`liquidate_ok: false`), leaving the position underwater but impossible to liquidate (`seized: false`).

## Flag
`H7CTF{a15a8281-06b7-43e7-908c-60da6e0ac849}`
