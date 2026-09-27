# Exploit Solution

This directory contains a working exploit for the Token Vault challenge.

## Building the Exploit

```bash
cd solve
make
```

This will create `target/deploy/solve.so`.

## Running the Exploit

From the challenge root directory:

```bash
python3 solve.py <server-ip> <port>
```

Example:
```bash
python3 solve.py localhost 5000
```

## How It Works

1. Deposits 100 lamports to reach VIP threshold
2. Calls pay_fee which triggers integer underflow (100 - 150 wraps around)
3. Withdraws the massive balance created by the underflow
4. User balance now exceeds 1,000,000 lamports → flag!

See SOLUTION.md for detailed explanation.
