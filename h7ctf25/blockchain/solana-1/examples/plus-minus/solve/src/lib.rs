pub mod processor;

use solana_program::entrypoint;
use processor::process_instruction;

entrypoint!(process_instruction);
