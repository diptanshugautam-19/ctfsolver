mod entrypoint;
pub mod processor;

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    instruction::{AccountMeta, Instruction},
    pubkey::Pubkey,
    system_program,
};

use std::mem::size_of;

/// Instructions supported by the Token Vault program
#[derive(BorshDeserialize, BorshSerialize, Debug)]
pub enum VaultInstruction {
    /// Initialize a vault for a user
    /// 
    /// Accounts:
    /// 0. [writable] Vault PDA account
    /// 1. [signer] User account
    /// 2. [] System program
    Initialize { vault_bump: u8 },

    /// Deposit lamports into the vault
    /// 
    /// Accounts:
    /// 0. [writable] Vault PDA account  
    /// 1. [writable, signer] User account
    /// 2. [] System program
    Deposit { amount: u64 },

    /// Withdraw all lamports from the vault
    /// 
    /// Accounts:
    /// 0. [writable] Vault PDA account
    /// 1. [writable, signer] User account
    Withdraw,

    /// Pay maintenance fee (VIP feature - requires 100+ lamports)
    /// 
    /// Accounts:
    /// 0. [writable] Vault PDA account
    /// 1. [signer] User account
    PayFee,
}

/// User's vault account data structure
#[repr(C)]
#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Vault {
    pub user: Pubkey,
    pub balance: u64,
    pub bump: u8,
}

pub const VAULT_SIZE: usize = size_of::<Vault>();
pub const MAINTENANCE_FEE: u64 = 150;
pub const VIP_THRESHOLD: u64 = 100;

/// Get the vault PDA for a user
pub fn get_vault(program_id: Pubkey, user: Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[b"VAULT", user.as_ref()], &program_id)
}

/// Create Initialize instruction
pub fn initialize(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, vault_bump) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::id(), false),
        ],
        data: VaultInstruction::Initialize { vault_bump }
            .try_to_vec()
            .unwrap(),
    }
}

/// Create Deposit instruction
pub fn deposit(program_id: Pubkey, user: Pubkey, amount: u64) -> Instruction {
    let (vault, _) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::id(), false),
        ],
        data: VaultInstruction::Deposit { amount }
            .try_to_vec()
            .unwrap(),
    }
}

/// Create Withdraw instruction
pub fn withdraw(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, _) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
        ],
        data: VaultInstruction::Withdraw.try_to_vec().unwrap(),
    }
}

/// Create PayFee instruction
pub fn pay_fee(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, _) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
        ],
        data: VaultInstruction::PayFee.try_to_vec().unwrap(),
    }
}
