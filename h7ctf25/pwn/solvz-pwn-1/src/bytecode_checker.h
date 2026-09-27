#ifndef BYTECODE_CHECKER_H_
#define BYTECODE_CHECKER_H_

#include <stdbool.h>

#define MAX_FILE_SIZE (1ul * 1024 * 1024)

#define WORK_DIR "workspace"
#define TRANS_NAME "transformer"
#define INPUT_NAME "input_code"
#define BINARY_NAME "output"

bool verify_bytecode(const unsigned char* buf, size_t size);
unsigned long execute_bytecode(void* buf);

#endif // BYTECODE_CHECKER_H_
