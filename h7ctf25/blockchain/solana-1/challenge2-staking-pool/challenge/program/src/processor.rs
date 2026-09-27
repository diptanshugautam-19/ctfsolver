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

use crate::{StakingInstruction, StakingPool};

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = StakingInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::InvalidInstructionData)?;

    match instruction {
        StakingInstruction::Initialize {
            organization,
            employee_id,
        } => initialize(program_id, accounts, organization, employee_id),
        StakingInstruction::Stake { amount } => stake(program_id, accounts, amount),
        StakingInstruction::Withdraw { amount } => withdraw(program_id, accounts, amount),
    }
}

fn initialize(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    organization: String,
    employee_id: String,
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let pool_account = next_account_info(accounts_iter)?;
    let authority = next_account_info(accounts_iter)?;
    let system_program = next_account_info(accounts_iter)?;

    // VULNERABILITY: PDA seed collision!
    // Seeds: [b"POOL", organization.as_bytes(), employee_id.as_bytes()]
    // Problem: "H7Corp" + "admin" = "H7Cor" + "padmin" (same bytes!)
    // This allows unauthorized access to admin pools!

    let (expected_pda, bump) = Pubkey::find_program_address(
        &[
            b"POOL",
            organization.as_bytes(),
            employee_id.as_bytes(),
        ],
        program_id,
    );

    if pool_account.key != &expected_pda {
        msg!("Error: Invalid pool PDA");
        return Err(ProgramError::InvalidSeeds);
    }

    // Check if admin
    let is_admin = organization == "H7Corp" && employee_id == "admin";

    // Create pool account
    let pool_data = StakingPool {
        organization: organization.clone(),
        employee_id: employee_id.clone(),
        total_staked: if is_admin { 100_000_000_000 } else { 0 }, // 100 SOL for admin
        is_admin,
    };

    let data_len = pool_data.try_to_vec()?.len();
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(data_len);

    invoke_signed(
        &system_instruction::create_account(
            authority.key,
            pool_account.key,
            lamports,
            data_len as u64,
            program_id,
        ),
        &[authority.clone(), pool_account.clone(), system_program.clone()],
        &[&[
            b"POOL",
            organization.as_bytes(),
            employee_id.as_bytes(),
            &[bump],
        ]],
    )?;

    pool_data.serialize(&mut &mut pool_account.data.borrow_mut()[..])?;

    msg!("Pool initialized for {}/{}", organization, employee_id);
    if is_admin {
        msg!("Admin pool created with 100 SOL!");
    }

    Ok(())
}

fn stake(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let pool_account = next_account_info(accounts_iter)?;
    let user = next_account_info(accounts_iter)?;
    let _system_program = next_account_info(accounts_iter)?;

    if !user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    if pool_account.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    let mut pool_data = StakingPool::try_from_slice(&pool_account.data.borrow())?;
    pool_data.total_staked += amount;
    pool_data.serialize(&mut &mut pool_account.data.borrow_mut()[..])?;

    // Transfer SOL from user to pool
    **user.try_borrow_mut_lamports()? -= amount;
    **pool_account.try_borrow_mut_lamports()? += amount;

    msg!("Staked {} lamports", amount);
    Ok(())
}

fn withdraw(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let pool_account = next_account_info(accounts_iter)?;
    let user = next_account_info(accounts_iter)?;

    if !user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    if pool_account.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    let mut pool_data = StakingPool::try_from_slice(&pool_account.data.borrow())?;

    if amount > pool_data.total_staked {
        msg!("Error: Insufficient staked balance");
        return Err(ProgramError::InsufficientFunds);
    }

    pool_data.total_staked -= amount;
    pool_data.serialize(&mut &mut pool_account.data.borrow_mut()[..])?;

    // Transfer SOL from pool to user
    **pool_account.try_borrow_mut_lamports()? -= amount;
    **user.try_borrow_mut_lamports()? += amount;

    msg!("Withdrawn {} lamports", amount);
    Ok(())
}
