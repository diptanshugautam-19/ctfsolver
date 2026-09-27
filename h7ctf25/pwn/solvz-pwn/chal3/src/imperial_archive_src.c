#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

int mauryan_empire = 0;
int ashoka_edict = 0;

void imperial_access() {
    if (mauryan_empire == 0x141 && ashoka_edict >= 0x397B) {
        printf("Glory to the Mauryan Empire! Access granted to the royal archives!\n");
        printf("Royal Inscription: \n");

        FILE *flag_file = fopen("flag.txt", "r");
    if (flag_file == NULL) {
        printf("Error: Failed to open flag.txt (errno: %d)\n", errno);
        exit(1);
    }

    char flag[256];
    if (fgets(flag, sizeof(flag), flag_file) == NULL) {
        printf("Error: Failed to read from flag.txt\n");
        fclose(flag_file);
        exit(1);
    }

    printf("Flag: %s", flag);
    fclose(flag_file);

        exit(0);
    } else {
        printf("Access denied.\n");
    }
}

void scribe_function() {
    char buffer[256];
    
    printf("Welcome to the Mauryan Imperial Authentication System\n");
    printf("Enter the royal inscription: ");
    fflush(stdout);
    
    if (fgets(buffer, sizeof(buffer), stdin) == NULL) {
        printf("Error reading inscription\n");
        exit(1);
    }

    buffer[strcspn(buffer, "\n")] = 0;
    
    printf("Processing inscription: ");
    printf(buffer);
    printf("\n");
    
    printf("Verifying imperial authority...\n");
    imperial_access();
}

int main() {
    setbuf(stdout, NULL);
    setbuf(stderr, NULL);
    
    printf("=== Mauryan Royal Archive v1.0 ===\n");
    scribe_function();
    
    return 0;
}