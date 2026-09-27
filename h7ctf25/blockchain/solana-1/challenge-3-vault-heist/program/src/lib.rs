pub mod entrypoint;
pub mod processor;

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    instruction::{AccountMeta, Instruction},
    pubkey::Pubkey,
    system_program,
};

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum VaultInstruction {
    /// Initialize a new vault
    /// 
    /// Accounts:
    /// 0. `[writable]` Vault PDA account
    /// 1. `[signer]` Vault authority (admin)
    /// 2. `[]` System program
    Initialize,

    /// Deposit lamports to the vault
    /// 
    /// Accounts:
    /// 0. `[writable]` Vault PDA account
    /// 1. `[signer, writable]` User account
    /// 2. `[]` System program
    Deposit { amount: u64 },

    /// Admin function to withdraw from vault
    /// WARNING: This function is VULNERABLE! 
    /// Missing signer check on admin account
    /// 
    /// Accounts:
    /// 0. `[writable]` Vault PDA account
    /// 1. `[writable]` Admin account (SHOULD be signer but isn't checked!)
    /// 2. `[writable]` Recipient account
    AdminWithdraw { amount: u64 },
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Vault {
    pub admin: Pubkey,
    pub total_deposited: u64,
}

// Helper functions to create instructions
pub fn initialize(
    program_id: Pubkey,
    vault_pda: Pubkey,
    admin: Pubkey,
) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault_pda, false),
            AccountMeta::new_readonly(admin, true),
            AccountMeta::new_readonly(system_program::ID, false),
        ],
        data: VaultInstruction::Initialize
            .try_to_vec()
            .unwrap(),
    }
}

pub fn deposit(
    program_id: Pubkey,
    vault_pda: Pubkey,
    user: Pubkey,
    amount: u64,
) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault_pda, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::ID, false),
        ],
        data: VaultInstruction::Deposit { amount }
            .try_to_vec()
            .unwrap(),
    }
}

pub fn admin_withdraw(
    program_id: Pubkey,
    vault_pda: Pubkey,
    admin: Pubkey,
    recipient: Pubkey,
    amount: u64,
) -> Instruction {
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault_pda, false),
            AccountMeta::new(admin, false), // VULNERABILITY: should be true (signer)!
            AccountMeta::new(recipient, false),
        ],
        data: VaultInstruction::AdminWithdraw { amount }
            .try_to_vec()
            .unwrap(),
    }
}

// Helper to derive vault PDA
pub fn get_vault_pda(program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[b"VAULT"], program_id)
}
