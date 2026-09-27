pub mod entrypoint;
pub mod processor;

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    instruction::{AccountMeta, Instruction},
    pubkey::Pubkey,
    system_program,
};

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum StakingInstruction {
    /// Initialize a new staking pool
    /// 
    /// Accounts:
    /// 0. `[writable]` Pool PDA account
    /// 1. `[signer]` Pool authority
    /// 2. `[]` System program
    Initialize {
        organization: String,
        employee_id: String,
    },

    /// Stake tokens to the pool
    /// 
    /// Accounts:
    /// 0. `[writable]` Pool PDA account
    /// 1. `[signer, writable]` User account
    /// 2. `[]` System program
    Stake { amount: u64 },

    /// Withdraw staked tokens
    /// 
    /// Accounts:
    /// 0. `[writable]` Pool PDA account
    /// 1. `[signer, writable]` User account
    Withdraw { amount: u64 },
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct StakingPool {
    pub organization: String,
    pub employee_id: String,
    pub total_staked: u64,
    pub is_admin: bool,
}

// Helper functions to create instructions
pub fn initialize(
    program_id: Pubkey,
    pool_pda: Pubkey,
    authority: Pubkey,
    organization: String,
    employee_id: String,
) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(pool_pda, false),
            AccountMeta::new_readonly(authority, true),
            AccountMeta::new_readonly(system_program::ID, false),
        ],
        data: StakingInstruction::Initialize {
            organization,
            employee_id,
        }
        .try_to_vec()
        .unwrap(),
    }
}

pub fn stake(program_id: Pubkey, pool_pda: Pubkey, user: Pubkey, amount: u64) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(pool_pda, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::ID, false),
        ],
        data: StakingInstruction::Stake { amount }
            .try_to_vec()
            .unwrap(),
    }
}

pub fn withdraw(program_id: Pubkey, pool_pda: Pubkey, user: Pubkey, amount: u64) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(pool_pda, false),
            AccountMeta::new(user, true),
        ],
        data: StakingInstruction::Withdraw { amount }
            .try_to_vec()
            .unwrap(),
    }
}

// Helper to derive pool PDA
pub fn get_pool_pda(program_id: &Pubkey, organization: &str, employee_id: &str) -> (Pubkey, u8) {
    Pubkey::find_program_address(
        &[
            b"POOL",
            organization.as_bytes(),
            employee_id.as_bytes(),
        ],
        program_id,
    )
}
