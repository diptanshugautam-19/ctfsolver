# H7Corp Token Vault

**Category:** Blockchain  
**Difficulty:** Easy  
**Points:** 300

## CTFd Description (Single Paragraph)

H7Corp operates a secure token vault system on Solana where users can deposit and withdraw lamports. The vault includes a VIP maintenance fee feature for users with at least 100 lamports in their vault. You start with 200 lamports. Grow your balance to 1,000,000 lamports or more to capture the flag. Download the source code, analyze the program, write your exploit, and submit the compiled .so file.

## Flag Format

`H7CTF{1nt3g3r_und3rfl0w_wr4ps_4r0und_<UUID>}`

## Flag Regex for CTFd

```regex
H7CTF\{1nt3g3r_und3rfl0w_wr4ps_4r0und_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}
```
