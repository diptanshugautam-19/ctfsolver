// gcc -o challenge test.c -no-pie -fno-stack-protector -lseccomp -O0 -w

/*
exploit structure

buffer overflow - ROP to mprotect
make stack executable
read shellcode to stack
stack pivoting
execute shellcode
shellcode to read flag from stack byte by byte (or bit by bit)

*/