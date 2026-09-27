use sol_ctf_framework::ChallengeBuilder;
use solana_program::system_program;
use solana_sdk::{
    account::Account,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
};
use borsh::BorshSerialize;
use std::{
    error::Error,
    fs,
    io::Write,
    net::{TcpListener, TcpStream},
};

const STARTING_BALANCE: u64 = 5_000_000_000;
const VAULT_BALANCE: u64 = 50_000_000_000;
const WIN_THRESHOLD: u64 = 40_000_000_000;
const SERVER_PORT: u16 = 5003;

#[derive(BorshSerialize)]
struct Vault {
    admin: Pubkey,
    total_deposited: u64,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let listener = TcpListener::bind(format!("0.0.0.0:{}", SERVER_PORT))?;
    println!("[*] Listening on 0.0.0.0:{}", SERVER_PORT);
    
    loop {
        let (stream, addr) = listener.accept()?;
        println!("[+] New connection from: {}", addr);
        
        tokio::spawn(async move {
            if let Err(e) = handle_connection(stream).await {
                eprintln!("[!] Handler error: {}", e);
            }
        });
    }
}

async fn handle_connection(mut socket: TcpStream) -> Result<(), Box<dyn Error>> {
    writeln!(socket, "Plus Minus")?;
    writeln!(socket, "Initializing challenge instance...")?;
    
    let mut builder = ChallengeBuilder::try_from(socket.try_clone().unwrap()).unwrap();

    let user = Keypair::new();
    
    let program_id = builder
        .add_program("./vault_heist.so", None)
        .expect("Failed to add vault program");

    let admin = Keypair::new();
    
    builder.builder.add_account(
        user.pubkey(),
        Account::new(STARTING_BALANCE, 0, &system_program::ID),
    );
    
    builder.builder.add_account(
        admin.pubkey(),
        Account::new(1_000_000_000, 0, &system_program::ID),
    );
    
    let (vault_pda, _) = Pubkey::find_program_address(
        &[b"VAULT"],
        &program_id,
    );
    
    let vault_data = Vault {
        admin: admin.pubkey(),
        total_deposited: VAULT_BALANCE,
    };
    
    let serialized_data = vault_data.try_to_vec().unwrap();
    
    let mut vault_account = Account::new(VAULT_BALANCE, serialized_data.len(), &program_id);
    vault_account.data = serialized_data;
    
    builder.builder.add_account(vault_pda, vault_account);
    
    writeln!(socket, "Player Account:")?;
    writeln!(socket, "  Address: {}", user.pubkey())?;
    writeln!(socket, "  Balance: {} SOL", STARTING_BALANCE / 1_000_000_000)?;
    
    let privkey_hex = user.to_bytes()
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>();
    writeln!(socket, "  Private Key: {}\n", privkey_hex)?;
    
    writeln!(socket, "Program:")?;
    writeln!(socket, "  Program ID: {}", program_id)?;
    writeln!(socket, "  Vault PDA: {}", vault_pda)?;
    writeln!(socket, "  Admin: {}\n", admin.pubkey())?;
    
    writeln!(socket, "Vault Status:")?;
    writeln!(socket, "  Balance: {} SOL", VAULT_BALANCE / 1_000_000_000)?;
    writeln!(socket, "  Admin: {}", admin.pubkey())?;
    
    writeln!(socket, "Objective: Withdraw {} SOL or more", WIN_THRESHOLD / 1_000_000_000)?;
    
    let solve_program_id = match builder.input_program() {
        Ok(pubkey) => pubkey,
        Err(e) => {
            writeln!(socket, "Error: cannot add solve program - {}", e)?;
            return Ok(());
        }
    };
    
    writeln!(socket, "Running exploit...")?;
    
    let mut challenge = builder.build().await;
    
    let balance_before = challenge
        .ctx
        .banks_client
        .get_account(user.pubkey())
        .await?
        .unwrap()
        .lamports;
    writeln!(socket, "Your balance before: {} SOL", balance_before / 1_000_000_000)?;
    
    let solve_ix = challenge.read_instruction(solve_program_id)?;
    challenge.run_ixs_full(&[solve_ix], &[&user], &user.pubkey()).await?;
    
    let balance_after = challenge
        .ctx
        .banks_client
        .get_account(user.pubkey())
        .await?
        .unwrap()
        .lamports;
    writeln!(socket, "Your balance: {} SOL", balance_after / 1_000_000_000)?;
    
    if balance_after >= WIN_THRESHOLD {
        let flag = fs::read_to_string("/home/ctfuser/flag.txt")
            .or_else(|_| fs::read_to_string("flag.txt"))
            .unwrap_or_else(|_| "H7CTF{test_flag}".to_string());
        writeln!(socket, "Flag: {}", flag.trim())?;
    } else {
        writeln!(socket, "Failed. Need {} SOL total.", WIN_THRESHOLD / 1_000_000_000)?;
    }

    Ok(())
}
