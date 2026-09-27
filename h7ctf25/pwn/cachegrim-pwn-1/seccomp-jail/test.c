#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <seccomp.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <string.h>


void setup_seccomp() {
    scmp_filter_ctx ctx;
    ctx = seccomp_init(SCMP_ACT_KILL);

    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(mprotect), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);

    seccomp_load(ctx);
}

void free_gadgets() {
    __asm__(".global pop_rdi_ret\n"
            "pop_rdi_ret:\n"
            "pop %rdi; ret;");

    __asm__(".global pop_rsi_ret\n"
            "pop_rsi_ret:\n"
            "pop %rsi; ret;");

    __asm__(".global pop_rdx_ret\n"
            "pop_rdx_ret:\n"
            "pop %rdx; ret;");

    __asm__(".global xchg_rax_rsp_ret\n"
            "xchg_rax_rsp_ret:\n"
            "xchg %rdi, %rsp; ret;");

    __asm__(".global pop_rax_ret\n"
            "pop_rax_ret:\n"
            "pop %rax; ret;");


    __asm__(".global add_rsp_ret\n"
            "add_rsp_ret:\n"
            "add $0x20, %rsp; ret;");

    __asm__(".global syscall_ret\n"
            "syscall_ret:\n"
            "syscall; ret;");

}

void vuln() {
    char buffer[64];
    char flag[128];
    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        perror("/flag file is missing");
        exit(1);
    }
    fread(flag, 1, sizeof(flag) - 1, fp);
    fclose(fp);

    printf("The flag file object is stored at: %p\n", &fp);
    printf("Enter input: ");
    read(0, buffer, 256);
//     setup_seccomp();s
}

int main() {
    setbuf(stdout, NULL);
    prctl(PR_SET_NO_NEW_PRIVS, 1);

    vuln();
    return 0;
}
