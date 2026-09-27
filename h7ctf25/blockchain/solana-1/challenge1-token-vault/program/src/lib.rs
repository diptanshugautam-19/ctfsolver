mod entrypoint;
pub mod processor;

use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    instruction::{AccountMeta, Instruction},
    pubkey::Pubkey,
    system_program,
};

/// Instructions supported by the Token Vault program
#[derive(BorshDeserialize, BorshSerialize, Debug)]
pub enum VaultInstruction {
    Initialize { vault_bump: u8 },
    Deposit { amount: u64 },
    Withdraw,
    PayFee,
}

/// Vault account data structure
#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Vault {
    pub user: Pubkey,
    pub balance: u64,
    pub bump: u8,
}

pub const VAULT_SIZE: usize = 41; // 32 (Pubkey) + 8 (u64) + 1 (u8) = 41 bytes
pub const MAINTENANCE_FEE: u64 = 150;
pub const VIP_THRESHOLD: u64 = 100;

pub fn get_vault(program_id: Pubkey, user: Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[b"VAULT", user.as_ref()], &program_id)
}

pub fn initialize(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, vault_bump) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::id(), false),
        ],
        data: VaultInstruction::Initialize { vault_bump }.try_to_vec().unwrap(),
    }
}

pub fn deposit(program_id: Pubkey, user: Pubkey, amount: u64) -> Instruction {
    let (vault, _) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
            AccountMeta::new_readonly(system_program::id(), false),
        ],
        data: VaultInstruction::Deposit { amount }.try_to_vec().unwrap(),
    }
}

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

pub fn pay_fee(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, _) = get_vault(program_id, user);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new_readonly(user, true),
        ],
        data: VaultInstruction::PayFee.try_to_vec().unwrap(),
    }
}
