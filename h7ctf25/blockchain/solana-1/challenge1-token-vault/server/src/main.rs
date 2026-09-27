use sol_ctf_framework::ChallengeBuilder;
use solana_program::system_program;
use solana_sdk::{
    account::Account,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
};
use std::{
    error::Error,
    fs,
    io::Write,
    net::{TcpListener, TcpStream},
};
use token_vault::initialize;

const STARTING_BALANCE: u64 = 10_000_000; // Enough for tx fees + deposits
const WIN_THRESHOLD: u64 = 1_000_000;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let listener = TcpListener::bind("0.0.0.0:5001")?;
    println!("[*] Listening on 0.0.0.0:5001");
    
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
    writeln!(socket, "╔════════════════════════════════════════════════╗")?;
    writeln!(socket, "║          H7CTF 2025 - Token Vault              ║")?;
    writeln!(socket, "╚════════════════════════════════════════════════╝\n")?;
    
    writeln!(socket, "Initializing challenge instance...\n")?;
    
    let mut builder = ChallengeBuilder::try_from(socket.try_clone()?)?;

    let user = Keypair::new();
    let user_pubkey = user.pubkey();

    let program_id = Pubkey::new_unique();
    let program_pubkey = builder
        .add_program("./token_vault.so", Some(program_id))
        .expect("Failed to add vault program");

    builder.builder.add_account(
        user_pubkey,
        Account::new(STARTING_BALANCE, 0, &system_program::ID),
    );

    let (vault_pda, _bump) = Pubkey::find_program_address(
        &[b"VAULT", user_pubkey.as_ref()], 
        &program_pubkey
    );

    writeln!(socket, "Instance ready.\n")?;
    
    writeln!(socket, "User Account:")?;
    writeln!(socket, "  Address: {}", user_pubkey)?;
    writeln!(socket, "  Balance: {} lamports", STARTING_BALANCE)?;
    
    let privkey_hex = user.to_bytes()
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>();
    writeln!(socket, "  Private Key: {}\n", privkey_hex)?;
    
    writeln!(socket, "Program:")?;
    writeln!(socket, "  Program ID: {}", program_pubkey)?;
    writeln!(socket, "  Vault PDA: {}\n", vault_pda)?;
    
    writeln!(socket, "Objective: Grow your balance to {} lamports or more.\n", WIN_THRESHOLD)?;
    writeln!(socket, "═══════════════════════════════════════════════\n")?;
    
    let solve_pubkey = match builder.input_program() {
        Ok(pubkey) => pubkey,
        Err(e) => {
            writeln!(socket, "Error: cannot add solve program - {}", e)?;
            return Ok(());
        }
    };
    
    let mut challenge = builder.build().await;

    challenge
        .run_ixs_full(
            &[initialize(program_pubkey, user_pubkey)],
            &[&user],
            &user_pubkey,
        )
        .await?;

    writeln!(socket, "\nRunning exploit...\n")?;
    let ixs = challenge.read_instruction(solve_pubkey).unwrap();
    challenge.run_ixs_full(&[ixs], &[&user], &user_pubkey).await?;

    let user_balance = challenge
        .ctx
        .banks_client
        .get_account(user_pubkey)
        .await?
        .unwrap()
        .lamports;
    
    let stolen = user_balance.saturating_sub(STARTING_BALANCE);
    
    writeln!(socket, "Results:")?;
    writeln!(socket, "  Your balance: {} lamports", user_balance)?;
    writeln!(socket, "  Gain: {} lamports", stolen)?;

    if stolen >= WIN_THRESHOLD {
        let flag = fs::read_to_string("/home/ctfuser/flag.txt")
            .or_else(|_| fs::read_to_string("flag.txt"))
            .unwrap_or_else(|_| "H7CTF{integer_underfl0w_makes_y0u_rich_82f93a}".to_string());
        writeln!(socket, "\nSuccess! Flag: {}\n", flag.trim())?;
    } else {
        writeln!(socket, "\nFailed. Need {} more lamports.\n", WIN_THRESHOLD - stolen)?;
    }

    Ok(())
}
