#define _GNU_SOURCE
#include <err.h>
#include <stdbool.h>
#include <stddef.h>

#include "bytecode_checker.h"

/* Reference: http://ref.x86asm.net/coder64.html */

#define ARRAY_LEN(a) (sizeof(a) / sizeof(a[0]))

struct modrm {
    union {
        struct {
            unsigned rm:3;
            unsigned reg:3;
            unsigned mod:2;
        };
        unsigned val;
    };
};

static bool verify_binop(const unsigned char* buf, size_t offset) {
    (void)offset;
    struct modrm modrm = { .val = buf[1] };

    if (modrm.mod == 0b00) {
        if (modrm.reg == 0b100) {
            return false;
        }
        if (modrm.rm == 0b100 || modrm.rm == 0b101) {
            return false;
        }
        return true;
    } else if (modrm.mod == 0b11) {
        if (modrm.reg == 0b100) {
            return false;
        }
        if (modrm.rm == 0b100) {
            return false;
        }
        return true;
    }

    return false;
}

static bool verify_unary_ops(const unsigned char* buf, size_t offset) {
    (void)offset;
    struct modrm modrm = { .val = buf[1] };

    switch (modrm.reg) {
        case 2: // not
        case 3: // neg
        case 4: // mul
        case 5: // imul
        case 6: // div
        case 7: // idiv
            if (modrm.mod == 0b00) {
                if (modrm.rm == 0b100 || modrm.rm == 0b101) {
                    return false;
                }
                return true;
            } else if (modrm.mod == 0b11) {
                if (modrm.rm == 0b100) {
                    return false;
                }
                return true;
            }
            return false;
        default:
            return false;
    }
}

static bool verify_shift_ops(const unsigned char* buf, size_t offset) {
    (void)offset;
    struct modrm modrm = { .val = buf[1] };

    switch (modrm.reg) {
        case 4: // shl/sal
        case 5: // shr
        case 7: // sar
            if (modrm.mod == 0b00) {
                if (modrm.rm == 0b100 || modrm.rm == 0b101) {
                    return false;
                }
                return true;
            } else if (modrm.mod == 0b11) {
                if (modrm.rm == 0b100) {
                    return false;
                }
                return true;
            }
            return false;
        default:
            return false;
    }
}

struct {
    unsigned char opcode;
    size_t size;
    bool (*verifier)(const unsigned char* buf, size_t offset);
} allowed_opcodes[] = {
    { 0x01, 2, verify_binop },    // add
    { 0x09, 2, verify_binop },    // or
    { 0x11, 2, verify_binop },    // adc
    { 0x19, 2, verify_binop },    // sbb
    { 0x21, 2, verify_binop },    // and
    { 0x29, 2, verify_binop },    // sub
    { 0x31, 2, verify_binop },    // xor
    { 0x39, 2, verify_binop },    // cmp
    { 0x85, 2, verify_binop },    // test
    { 0x87, 2, verify_binop },    // xchg
    { 0x89, 2, verify_binop },    // mov
    { 0x8b, 2, verify_binop },    // mov
    { 0x90, 1, NULL },            // nop
    { 0xb8, 5, NULL },            // mov eax, imm32
    { 0xb9, 5, NULL },            // mov ecx, imm32
    { 0xba, 5, NULL },            // mov edx, imm32
    { 0xbb, 5, NULL },            // mov ebx, imm32
    { 0xbc, 5, NULL },            // mov esp, imm32
    { 0xbd, 5, NULL },            // mov ebp, imm32
    { 0xbe, 5, NULL },            // mov esi, imm32
    { 0xbf, 5, NULL },            // mov edi, imm32
    { 0xc1, 3, verify_shift_ops },// shift operations with immediate
    { 0xc3, 1, NULL },            // ret
    { 0xd1, 2, verify_shift_ops },// shift operations by 1
    { 0xd3, 2, verify_shift_ops },// shift operations by CL
    { 0xf7, 2, verify_unary_ops },// unary operations
};

bool verify_bytecode(const unsigned char* buf, size_t size) {
    size_t i = 0;
    while (i < size) {
        bool ok = false;
        for (size_t idx = 0; idx < ARRAY_LEN(allowed_opcodes); ++idx) {
            if (buf[i] == allowed_opcodes[idx].opcode) {
                if (i + allowed_opcodes[idx].size > size) {
                    return false;
                }
                if (allowed_opcodes[idx].verifier && !allowed_opcodes[idx].verifier(&buf[i], i)) {
                    return false;
                }
                i += allowed_opcodes[idx].size;
                ok = true;
                break;
            }
        }
        if (!ok) {
            return false;
        }
    }
    if (i != size) {
        return false;
    }

    return true;
}
