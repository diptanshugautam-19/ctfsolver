use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

use crate::{Vault, VaultInstruction, MAINTENANCE_FEE, VAULT_SIZE, VIP_THRESHOLD};

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = VaultInstruction::try_from_slice(instruction_data)?;

    match instruction {
        VaultInstruction::Initialize { vault_bump } => {
            process_initialize(program_id, accounts, vault_bump)
        }
        VaultInstruction::Deposit { amount } => process_deposit(program_id, accounts, amount),
        VaultInstruction::Withdraw => process_withdraw(program_id, accounts),
        VaultInstruction::PayFee => process_pay_fee(program_id, accounts),
    }
}

/// Initialize a new vault for a user
fn process_initialize(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    vault_bump: u8,
) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_iter)?;
    let user_account = next_account_info(account_iter)?;
    let system_program = next_account_info(account_iter)?;

    // Verify user is signer
    if !user_account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Verify vault PDA
    let vault_seeds = &[b"VAULT", user_account.key.as_ref(), &[vault_bump]];
    let vault_pda = Pubkey::create_program_address(vault_seeds, program_id)?;
    
    if vault_pda != *vault_account.key {
        msg!("Invalid vault PDA");
        return Err(ProgramError::InvalidSeeds);
    }

    // Check vault account is empty
    if !vault_account.data_is_empty() {
        msg!("Vault already initialized");
        return Err(ProgramError::AccountAlreadyInitialized);
    }

    // Create vault account
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(VAULT_SIZE);

    invoke_signed(
        &system_instruction::create_account(
            user_account.key,
            vault_account.key,
            lamports,
            VAULT_SIZE as u64,
            program_id,
        ),
        &[user_account.clone(), vault_account.clone(), system_program.clone()],
        &[vault_seeds],
    )?;

    // Initialize vault data
    let vault = Vault {
        user: *user_account.key,
        balance: 0,
        bump: vault_bump,
    };

    vault.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;

    msg!("Vault initialized for user: {}", user_account.key);
    Ok(())
}

/// Deposit lamports into the vault
fn process_deposit(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_iter)?;
    let user_account = next_account_info(account_iter)?;
    let system_program = next_account_info(account_iter)?;

    // Verify user is signer
    if !user_account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Verify vault ownership
    if vault_account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Debug: log vault account info
    msg!("DEBUG: Vault account owner: {}", vault_account.owner);
    msg!("DEBUG: Vault account data len: {}", vault_account.data_len());
    msg!("DEBUG: Vault account lamports: {}", vault_account.lamports());
    msg!("DEBUG: Expected program_id: {}", program_id);
    
    // Deserialize vault
    let mut vault = Vault::try_from_slice(&vault_account.data.borrow())?;

    // Verify vault belongs to user
    if vault.user != *user_account.key {
        msg!("Vault does not belong to user");
        return Err(ProgramError::InvalidAccountData);
    }

    // Verify amount is reasonable
    if amount == 0 {
        msg!("Deposit amount must be greater than 0");
        return Err(ProgramError::InvalidArgument);
    }

    // Transfer lamports from user to vault (stored in vault PDA)
    solana_program::program::invoke(
        &system_instruction::transfer(user_account.key, vault_account.key, amount),
        &[user_account.clone(), vault_account.clone(), system_program.clone()],
    )?;

    // Update vault balance
    vault.balance += amount;
    vault.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;

    msg!("Deposited {} lamports. New balance: {}", amount, vault.balance);
    Ok(())
}

/// Withdraw all lamports from the vault
fn process_withdraw(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_iter)?;
    let user_account = next_account_info(account_iter)?;

    // Verify user is signer
    if !user_account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Verify vault ownership
    if vault_account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Deserialize vault
    let mut vault = Vault::try_from_slice(&vault_account.data.borrow())?;

    // Verify vault belongs to user
    if vault.user != *user_account.key {
        msg!("Vault does not belong to user");
        return Err(ProgramError::InvalidAccountData);
    }

    // Check if there's anything to withdraw
    if vault.balance == 0 {
        msg!("No balance to withdraw");
        return Err(ProgramError::InsufficientFunds);
    }

    let withdraw_amount = vault.balance;

    // Transfer lamports from vault PDA back to user
    **vault_account.try_borrow_mut_lamports()? -= withdraw_amount;
    **user_account.try_borrow_mut_lamports()? += withdraw_amount;

    // Reset vault balance
    vault.balance = 0;
    vault.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;

    msg!("Withdrew {} lamports", withdraw_amount);
    Ok(())
}

fn process_pay_fee(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_iter)?;
    let user_account = next_account_info(account_iter)?;

    // Verify user is signer
    if !user_account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Verify vault ownership
    if vault_account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Deserialize vault
    let mut vault = Vault::try_from_slice(&vault_account.data.borrow())?;

    // Verify vault belongs to user
    if vault.user != *user_account.key {
        msg!("Vault does not belong to user");
        return Err(ProgramError::InvalidAccountData);
    }

    // VIP feature: Only users with >= 100 lamports can use this
    if vault.balance >= VIP_THRESHOLD {
        msg!("Processing VIP maintenance fee");
        vault.balance -= MAINTENANCE_FEE;
        
        vault.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;
        msg!("Fee paid. New balance: {}", vault.balance);
        Ok(())
    } else {
        msg!(
            "Insufficient balance for VIP features. Need at least {} lamports, have {}",
            VIP_THRESHOLD,
            vault.balance
        );
        Err(ProgramError::InsufficientFunds)
    }
}
