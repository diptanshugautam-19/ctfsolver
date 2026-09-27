#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

char flag[100];

void load_flag() {
    FILE *f = fopen("flag.txt", "r");
    if (!f) {
        perror("flag");
        exit(1);
    }
    if (fgets(flag, sizeof(flag), f) == NULL) {
        perror("reading flag");
        exit(1);
    }
    fclose(f);

    size_t len = strlen(flag);
    if (len > 0 && flag[len-1] == '\n') {
        flag[len-1] = '\0';
    }
}

void menu() {
    puts("Welcome to 0verf10w!");
    puts("1) Echo");
    puts("2) Get Flag");
    puts("3) Quit");
    printf("Choice: ");
    fflush(stdout);
}

void win() {
    printf("Here's your flag: %s\n", flag);
    fflush(stdout);
}

void echo() {
    int authenticated = 0;
    char buf[64];
    
    printf("Say something: ");
    fflush(stdout);
    
    gets(buf);
    
    printf("You said: %s\n", buf);
    
    if (authenticated) {
        printf("Authentication bypassed!\n");
        win();
    }
}

void get_flag() {
    puts("You are not authenticated.");
    puts("Try the echo function to see if you can bypass authentication!");
    fflush(stdout);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    
    load_flag();
    
    while (1) {
        menu();
        char choice[4];
        if (fgets(choice, sizeof(choice), stdin) == NULL) {
            break;
        }
        
        switch (atoi(choice)) {
            case 1:
                echo();
                break;
            case 2:
                get_flag();
                break;
            case 3:
                puts("Bye!");
                exit(0);
            default:
                puts("Invalid choice");
        }
    }
    return 0;
}
