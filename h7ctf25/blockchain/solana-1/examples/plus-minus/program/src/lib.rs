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
    Initialize,
    Deposit { amount: u64 },
    AdminWithdraw { amount: u64 },
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Vault {
    pub admin: Pubkey,
    pub total_deposited: u64,
}

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
            AccountMeta::new(admin, false),
            AccountMeta::new(recipient, false),
        ],
        data: VaultInstruction::AdminWithdraw { amount }
            .try_to_vec()
            .unwrap(),
    }
}

pub fn get_vault_pda(program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(&[b"VAULT"], program_id)
}
