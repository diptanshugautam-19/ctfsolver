use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    msg,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
    system_instruction,
    sysvar::{rent::Rent, Sysvar},
};

use crate::{Vault, VaultInstruction};

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = VaultInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::InvalidInstructionData)?;

    match instruction {
        VaultInstruction::Initialize => {
            msg!("Instruction: Initialize");
            process_initialize(program_id, accounts)
        }
        VaultInstruction::Deposit { amount } => {
            msg!("Instruction: Deposit");
            process_deposit(program_id, accounts, amount)
        }
        VaultInstruction::AdminWithdraw { amount } => {
            msg!("Instruction: AdminWithdraw");
            process_admin_withdraw(program_id, accounts, amount)
        }
    }
}

fn process_initialize(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_info_iter)?;
    let admin_account = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Verify admin is signer
    if !admin_account.is_signer {
        msg!("Admin must be signer for initialization");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Derive PDA
    let (vault_pda, bump) = Pubkey::find_program_address(&[b"VAULT"], program_id);
    
    if vault_pda != *vault_account.key {
        msg!("Invalid vault PDA");
        return Err(ProgramError::InvalidAccountData);
    }

    // Create vault account
    let rent = Rent::get()?;
    let vault_size = std::mem::size_of::<Vault>();
    let rent_lamports = rent.minimum_balance(vault_size);

    invoke_signed(
        &system_instruction::create_account(
            admin_account.key,
            vault_account.key,
            rent_lamports,
            vault_size as u64,
            program_id,
        ),
        &[admin_account.clone(), vault_account.clone(), system_program.clone()],
        &[&[b"VAULT", &[bump]]],
    )?;

    let vault_data = Vault {
        admin: *admin_account.key,
        total_deposited: 0,
    };

    vault_data.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;

    msg!("Vault initialized with admin: {}", admin_account.key);
    Ok(())
}

fn process_deposit(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_info_iter)?;
    let user_account = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Verify user is signer
    if !user_account.is_signer {
        msg!("User must be signer for deposit");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Verify vault PDA
    let (vault_pda, _) = Pubkey::find_program_address(&[b"VAULT"], program_id);
    if vault_pda != *vault_account.key {
        msg!("Invalid vault PDA");
        return Err(ProgramError::InvalidAccountData);
    }

    // Transfer lamports to vault
    invoke_signed(
        &system_instruction::transfer(user_account.key, vault_account.key, amount),
        &[user_account.clone(), vault_account.clone(), system_program.clone()],
        &[],
    )?;

    // Update vault data
    let mut vault_data = Vault::try_from_slice(&vault_account.data.borrow())?;
    vault_data.total_deposited += amount;
    vault_data.serialize(&mut &mut vault_account.data.borrow_mut()[..])?;

    msg!("Deposited {} lamports to vault", amount);
    Ok(())
}

fn process_admin_withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let vault_account = next_account_info(account_info_iter)?;
    let admin_account = next_account_info(account_info_iter)?;
    let recipient_account = next_account_info(account_info_iter)?;

    let (vault_pda, _bump) = Pubkey::find_program_address(&[b"VAULT"], program_id);
    if vault_pda != *vault_account.key {
        msg!("Invalid vault PDA");
        return Err(ProgramError::InvalidAccountData);
    }

    let vault_data = Vault::try_from_slice(&vault_account.data.borrow())?;

    // VULNERABILITY: Missing signer check!
    // The code checks if the provided admin_account matches the stored admin pubkey,
    // but it does NOT verify that admin_account.is_signer == true!
    // This means ANYONE can call this function and pass in the admin's pubkey
    // without actually having the admin's private key.
    
    if vault_data.admin != *admin_account.key {
        msg!("Only admin can withdraw from vault");
        return Err(ProgramError::InvalidAccountData);
    }

    // Check vault has enough lamports
    if **vault_account.lamports.borrow() < amount {
        msg!("Insufficient funds in vault");
        return Err(ProgramError::InsufficientFunds);
    }

    // Transfer lamports from vault to recipient using PDA signature
    **vault_account.lamports.borrow_mut() -= amount;
    **recipient_account.lamports.borrow_mut() += amount;

    msg!("Admin withdrew {} lamports from vault to {}", amount, recipient_account.key);
    Ok(())
}
