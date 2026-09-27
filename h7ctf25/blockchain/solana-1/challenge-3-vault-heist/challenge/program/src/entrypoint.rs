use solana_program::entrypoint;

entrypoint!(process_instruction);

fn process_instruction(
    program_id: &solana_program::pubkey::Pubkey,
    accounts: &[solana_program::account_info::AccountInfo],
    instruction_data: &[u8],
) -> solana_program::entrypoint::ProgramResult {
    crate::processor::process_instruction(program_id, accounts, instruction_data)
}
