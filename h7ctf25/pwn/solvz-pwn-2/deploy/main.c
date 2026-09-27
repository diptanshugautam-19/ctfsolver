#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <stdint.h>

#define MAX_CHUNKS 16
#define CHUNK_SIZE 0x100
#define POOL_SIZE (MAX_CHUNKS * CHUNK_SIZE + 0x1000)

typedef struct {
    void *pool_base;
    size_t pool_size;
    uint64_t chunk_bitmap;
    void *chunks[MAX_CHUNKS];
} MemoryPool;

MemoryPool g_pool = {0};

void init_pool() {
    g_pool.pool_base = mmap(NULL, POOL_SIZE, PROT_READ | PROT_WRITE | PROT_EXEC,
                            MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (g_pool.pool_base == MAP_FAILED) {
        perror("mmap");
        exit(1);
    }
    g_pool.pool_size = POOL_SIZE;
    g_pool.chunk_bitmap = 0;
    memset(g_pool.chunks, 0, sizeof(g_pool.chunks));
}

void* custom_malloc(size_t size) {
    if (size > CHUNK_SIZE) {
        printf("[-] Size too large\n");
        return NULL;
    }
    
    for (int i = 0; i < MAX_CHUNKS; i++) {
        if (!(g_pool.chunk_bitmap & (1ULL << i))) {
            void *chunk = g_pool.pool_base + (i * CHUNK_SIZE);
            g_pool.chunk_bitmap |= (1ULL << i);
            g_pool.chunks[i] = chunk;
            return chunk;
        }
    }
    
    printf("[-] Pool exhausted\n");
    return NULL;
}

void custom_free(void *ptr) {
    if (!ptr) return;
    
    for (int i = 0; i < MAX_CHUNKS; i++) {
        if (g_pool.chunks[i] == ptr) {
            g_pool.chunk_bitmap &= ~(1ULL << i);
            return;
        }
    }
    
    printf("[-] Invalid pointer\n");
}

typedef struct {
    char name[32];
    void (*print_func)(void*);
    char data[CHUNK_SIZE - 32 - 8];
} DataNode;

void print_data(void *node) {
    DataNode *n = (DataNode*)node;
    printf("[+] Node: %s\n", n->name);
    printf("[+] Data: %s\n", n->data);
}

void gadget_pop_rdi() {
    __asm__("pop %rdi; ret;");
}

void gadget_pop_rsi() {
    __asm__("pop %rsi; ret;");
}

void gadget_pop_rdx() {
    __asm__("pop %rdx; ret;");
}

void gadget_syscall() {
    __asm__("syscall; ret;");
}

void gadget_pivot() {
    __asm__("mov %rsp, %rdi; ret;");
}

void leak_function() {
    printf("[*] Leak address: %p\n", leak_function);
    fflush(stdout);
}

DataNode *nodes[MAX_CHUNKS] = {0};

void menu() {
    printf("\n=== Quantum Memory Manager v2.0 ===\n");
    printf("1. Allocate quantum node\n");
    printf("2. Edit quantum node\n");
    printf("3. View quantum node\n");
    printf("4. Delete quantum node\n");
    printf("5. Leak info (debug)\n");
    printf("6. Exit\n");
    printf(">>> ");
    fflush(stdout);
}

void allocate_node() {
    int idx;
    printf("Index (0-%d): ", MAX_CHUNKS - 1);
    fflush(stdout);
    scanf("%d", &idx);
    getchar();
    
    if (idx < 0 || idx >= MAX_CHUNKS) {
        printf("[-] Invalid index\n");
        return;
    }
    
    if (nodes[idx]) {
        printf("[-] Slot already in use\n");
        return;
    }
    
    DataNode *node = (DataNode*)custom_malloc(sizeof(DataNode));
    if (!node) {
        printf("[-] Allocation failed\n");
        return;
    }
    
    printf("Name: ");
    fflush(stdout);
    fgets(node->name, sizeof(node->name), stdin);
    node->name[strcspn(node->name, "\n")] = 0;
    
    node->print_func = print_data;
    nodes[idx] = node;
    
    printf("[+] Node allocated at index %d\n", idx);
}

void edit_node() {
    int idx;
    size_t size;
    printf("Index: ");
    fflush(stdout);
    scanf("%d", &idx);
    getchar();
    
    if (idx < 0 || idx >= MAX_CHUNKS) {
        printf("[-] Invalid index\n");
        return;
    }
    
    if (!nodes[idx]) {
        printf("[-] No node at this index\n");
        return;
    }
    
    printf("Size (max %d): ", CHUNK_SIZE);
    fflush(stdout);
    scanf("%zu", &size);
    getchar();
    
    if (size > CHUNK_SIZE) {
        size = CHUNK_SIZE;
    }
    
    printf("Data: ");
    fflush(stdout);
    ssize_t n = read(STDIN_FILENO, nodes[idx]->data, size);
    if (n < 0) {
        printf("[-] Read error\n");
        return;
    }
    
    printf("[+] Node updated with %zd bytes\n", n);
}

void view_node() {
    int idx;
    printf("Index: ");
    fflush(stdout);
    scanf("%d", &idx);
    getchar();
    
    if (idx < 0 || idx >= MAX_CHUNKS) {
        printf("[-] Invalid index\n");
        return;
    }
    
    if (!nodes[idx]) {
        printf("[-] No node at this index\n");
        return;
    }
    
    if (nodes[idx]->print_func) {
        nodes[idx]->print_func(nodes[idx]);
    }
}

void delete_node() {
    int idx;
    printf("Index: ");
    fflush(stdout);
    scanf("%d", &idx);
    getchar();
    
    if (idx < 0 || idx >= MAX_CHUNKS) {
        printf("[-] Invalid index\n");
        return;
    }
    
    if (!nodes[idx]) {
        printf("[-] No node at this index\n");
        return;
    }
    
    custom_free(nodes[idx]);
    printf("[+] Node deleted\n");
}

void leak_info() {
    printf("[*] Pool base: %p\n", g_pool.pool_base);
    printf("[*] Print function: %p\n", print_data);
    printf("[*] Leak function: %p\n", leak_function);
    
    extern void *__libc_start_main;
    printf("[*] libc_start_main: %p\n", __libc_start_main);
    printf("[*] puts: %p\n", puts);
    fflush(stdout);
}

int main() {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    
    init_pool();
    
    printf("=== Welcome to Quantum Memory Manager ===\n");
    printf("[*] Advanced memory management for quantum computing simulations\n");
    
    int choice;
    while (1) {
        menu();
        
        if (scanf("%d", &choice) != 1) {
            printf("[-] Invalid input\n");
            break;
        }
        getchar();
        
        switch (choice) {
            case 1:
                allocate_node();
                break;
            case 2:
                edit_node();
                break;
            case 3:
                view_node();
                break;
            case 4:
                delete_node();
                break;
            case 5:
                leak_info();
                break;
            case 6:
                printf("[+] Goodbye!\n");
                return 0;
            default:
                printf("[-] Invalid choice\n");
        }
    }
    
    return 0;
}
