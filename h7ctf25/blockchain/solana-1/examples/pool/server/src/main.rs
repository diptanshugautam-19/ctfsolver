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

const STARTING_BALANCE: u64 = 10_000_000_000;
const ADMIN_POOL_BALANCE: u64 = 100_000_000_000;
const WIN_THRESHOLD: u64 = 50_000_000_000;
const SERVER_PORT: u16 = 5001;

#[derive(BorshSerialize)]
struct StakingPool {
    organization: String,
    employee_id: String,
    total_staked: u64,
    is_admin: bool,
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
    writeln!(socket, "Pool")?;
    writeln!(socket, "Initializing challenge instance...")?;
    
    let mut builder = ChallengeBuilder::try_from(socket.try_clone().unwrap()).unwrap();

    let user = Keypair::new();
    
    let program_id = builder
        .add_program("./staking_pool.so", None)
        .expect("Failed to add staking pool program");

    builder.builder.add_account(
        user.pubkey(),
        Account::new(STARTING_BALANCE, 0, &system_program::ID),
    );
    
    let admin_org = "H7Corp";
    let admin_emp = "admin";
    let (admin_pool_pda, _) = Pubkey::find_program_address(
        &[b"POOL", admin_org.as_bytes(), admin_emp.as_bytes()],
        &program_id,
    );
    
    let admin_pool_data = StakingPool {
        organization: admin_org.to_string(),
        employee_id: admin_emp.to_string(),
        total_staked: ADMIN_POOL_BALANCE,
        is_admin: true,
    };
    
    let serialized_data = admin_pool_data.try_to_vec().unwrap();
    
    let mut admin_account = Account::new(ADMIN_POOL_BALANCE, serialized_data.len(), &program_id);
    admin_account.data = serialized_data;
    
    builder.builder.add_account(admin_pool_pda, admin_account);
    
    writeln!(socket, "Player Account:")?;
    writeln!(socket, "  Address: {}", user.pubkey())?;
    writeln!(socket, "  Balance: {} SOL", STARTING_BALANCE / 1_000_000_000)?;
    
    let privkey_hex = user.to_bytes()
        .iter()
        .map(|b| format!("{:02x}", b))
        .collect::<String>();
    writeln!(socket, "  Private Key: {}\n", privkey_hex)?;
    
    writeln!(socket, "Program:")?;
    writeln!(socket, "  Program ID: {}\n", program_id)?;
    
    writeln!(socket, "Target:")?;
    writeln!(socket, "  Admin Pool: {}", admin_pool_pda)?;
    writeln!(socket, "  Balance: {} SOL", ADMIN_POOL_BALANCE / 1_000_000_000)?;
    writeln!(socket, "  Organization: {}", admin_org)?;
    writeln!(socket, "  Employee ID: {}", admin_emp)?;
    
    writeln!(socket, "Objective: Steal {} SOL or more", WIN_THRESHOLD / 1_000_000_000)?;
    
    let solve_pubkey = match builder.input_program() {
        Ok(pubkey) => pubkey,
        Err(e) => {
            writeln!(socket, "Error: cannot add solve program - {}", e)?;
            return Ok(());
        }
    };
    
    writeln!(socket, "Running exploit...")?;
    
    let mut challenge = builder.build().await;

    let solve_ix = challenge.read_instruction(solve_pubkey)?;
    
    challenge.run_ixs_full(&[solve_ix], &[&user], &user.pubkey()).await?;

    let user_balance = challenge
        .ctx
        .banks_client
        .get_account(user.pubkey())
        .await?
        .unwrap()
        .lamports;
    
    writeln!(socket, "Your balance: {} SOL", user_balance / 1_000_000_000)?;

    if user_balance >= WIN_THRESHOLD {
        let flag = fs::read_to_string("/home/ctfuser/flag.txt")
            .or_else(|_| fs::read_to_string("flag.txt"))
            .unwrap_or_else(|_| "H7CTF{test_flag}".to_string());
        writeln!(socket, "Flag: {}", flag.trim())?;
    } else {
        writeln!(socket, "Failed. Need {} SOL total.", WIN_THRESHOLD / 1_000_000_000)?;
    }

    Ok(())
}
