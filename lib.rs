use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program_error::ProgramError,
    pubkey::Pubkey,
};

pub const PRICE_SCALE: u128 = 1_000_000;
pub const LTV_NUM: u128 = 80;
pub const LTV_DEN: u128 = 100;

pub const OWNER_OFF: usize = 0;
pub const SEIZED_OFF: usize = 32;
pub const COUNT_OFF: usize = 33;
pub const HEADER: usize = 41;
pub const POS_SIZE: usize = 16;
pub const MAX_POSITIONS: usize = 20_000;

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Market {
    pub admin: Pubkey,
    pub price: u64,
    pub reserve: u64,
}

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum Ix {
    InitMarket { price: u64, reserve: u64 },
    SetPrice { price: u64 },
    InitObligation,
    OpenPosition { collateral: u64, debt: u64 },
    Liquidate,
    OpenMany { collateral: u64, debt: u64, count: u32 },
}

pub fn healthy(collateral: u128, debt: u128, price: u128) -> bool {
    let value = collateral.saturating_mul(price) / PRICE_SCALE;
    debt <= value.saturating_mul(LTV_NUM) / LTV_DEN
}

fn rd_u64(data: &[u8], off: usize) -> u64 {
    u64::from_le_bytes(data[off..off + 8].try_into().unwrap())
}

fn wr_u64(data: &mut [u8], off: usize, v: u64) {
    data[off..off + 8].copy_from_slice(&v.to_le_bytes());
}

fn read_market(ai: &AccountInfo) -> Result<Market, ProgramError> {
    let data = ai.data.borrow();
    let mut slice: &[u8] = &data[..];
    Market::deserialize(&mut slice).map_err(|_| ProgramError::InvalidAccountData)
}

fn write_market(ai: &AccountInfo, m: &Market) -> Result<(), ProgramError> {
    let mut buf = Vec::new();
    m.serialize(&mut buf).map_err(|_| ProgramError::InvalidAccountData)?;
    let mut data = ai.data.borrow_mut();
    if buf.len() > data.len() {
        return Err(ProgramError::AccountDataTooSmall);
    }
    data[..buf.len()].copy_from_slice(&buf);
    Ok(())
}

pub fn process(_program_id: &Pubkey, accounts: &[AccountInfo], input: &[u8]) -> ProgramResult {
    let ix = Ix::try_from_slice(input).map_err(|_| ProgramError::InvalidInstructionData)?;
    let it = &mut accounts.iter();
    match ix {
        Ix::InitMarket { price, reserve } => {
            let market = next_account_info(it)?;
            let admin = next_account_info(it)?;
            write_market(market, &Market { admin: *admin.key, price, reserve })?;
        }
        Ix::SetPrice { price } => {
            let market = next_account_info(it)?;
            let admin = next_account_info(it)?;
            let mut m = read_market(market)?;
            if m.admin != *admin.key || !admin.is_signer {
                return Err(ProgramError::MissingRequiredSignature);
            }
            m.price = price;
            write_market(market, &m)?;
        }
        Ix::InitObligation => {
            let obligation = next_account_info(it)?;
            let owner = next_account_info(it)?;
            let mut data = obligation.data.borrow_mut();
            if data.len() < HEADER {
                return Err(ProgramError::AccountDataTooSmall);
            }
            data[OWNER_OFF..OWNER_OFF + 32].copy_from_slice(owner.key.as_ref());
            data[SEIZED_OFF] = 0;
            wr_u64(&mut data, COUNT_OFF, 0);
        }
        Ix::OpenPosition { collateral, debt } => {
            let market = next_account_info(it)?;
            let obligation = next_account_info(it)?;
            let owner = next_account_info(it)?;
            let m = read_market(market)?;
            if !healthy(collateral as u128, debt as u128, m.price as u128) {
                return Err(ProgramError::InvalidArgument);
            }
            let mut data = obligation.data.borrow_mut();
            if &data[OWNER_OFF..OWNER_OFF + 32] != owner.key.as_ref() || !owner.is_signer {
                return Err(ProgramError::MissingRequiredSignature);
            }
            let count = rd_u64(&data, COUNT_OFF) as usize;
            if count + 1 > MAX_POSITIONS {
                return Err(ProgramError::InvalidArgument);
            }
            let off = HEADER + count * POS_SIZE;
            if off + POS_SIZE > data.len() {
                return Err(ProgramError::AccountDataTooSmall);
            }
            wr_u64(&mut data, off, collateral);
            wr_u64(&mut data, off + 8, debt);
            wr_u64(&mut data, COUNT_OFF, (count + 1) as u64);
        }
        Ix::Liquidate => {
            let market = next_account_info(it)?;
            let obligation = next_account_info(it)?;
            let m = read_market(market)?;
            let mut data = obligation.data.borrow_mut();
            let price = m.price as u128;
            let count = rd_u64(&data, COUNT_OFF) as usize;
            let mut allowed_debt: u128 = 0;
            let mut total_debt: u128 = 0;
            for i in 0..count {
                let off = HEADER + i * POS_SIZE;
                let value = (rd_u64(&data, off) as u128).saturating_mul(price) / PRICE_SCALE;
                allowed_debt = allowed_debt.saturating_add(value.saturating_mul(LTV_NUM) / LTV_DEN);
                total_debt = total_debt.saturating_add(rd_u64(&data, off + 8) as u128);
            }
            if total_debt <= allowed_debt {
                return Err(ProgramError::InvalidArgument);
            }
            data[SEIZED_OFF] = 1;
        }
        Ix::OpenMany { collateral, debt, count } => {
            let market = next_account_info(it)?;
            let obligation = next_account_info(it)?;
            let owner = next_account_info(it)?;
            let m = read_market(market)?;
            if !healthy(collateral as u128, debt as u128, m.price as u128) {
                return Err(ProgramError::InvalidArgument);
            }
            let mut data = obligation.data.borrow_mut();
            if &data[OWNER_OFF..OWNER_OFF + 32] != owner.key.as_ref() || !owner.is_signer {
                return Err(ProgramError::MissingRequiredSignature);
            }
            let mut n = rd_u64(&data, COUNT_OFF) as usize;
            if n + (count as usize) > MAX_POSITIONS {
                return Err(ProgramError::InvalidArgument);
            }
            for _ in 0..count {
                let off = HEADER + n * POS_SIZE;
                if off + POS_SIZE > data.len() {
                    return Err(ProgramError::AccountDataTooSmall);
                }
                wr_u64(&mut data, off, collateral);
                wr_u64(&mut data, off + 8, debt);
                n += 1;
            }
            wr_u64(&mut data, COUNT_OFF, n as u64);
        }
    }
    Ok(())
}

#[cfg(not(feature = "no-entrypoint"))]
solana_program::entrypoint!(entry);
#[cfg(not(feature = "no-entrypoint"))]
pub fn entry(program_id: &Pubkey, accounts: &[AccountInfo], input: &[u8]) -> ProgramResult {
    process(program_id, accounts, input)
}
