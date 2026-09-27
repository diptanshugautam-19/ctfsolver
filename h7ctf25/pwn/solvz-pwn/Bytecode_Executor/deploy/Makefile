CFLAGS = -std=c11 -Wall -Wextra -Werror

all: main

main: main.o verifier.o executor.o
	gcc $(CFLAGS) -o $@ $^

executor.o: %.o: %.asm
	nasm -felf64 -o $@ $^

%.o: %.c
	gcc $(CFLAGS) -o $@ -c $^

.PHONY: clean
clean:
	rm -rf *.o main workspace/

.PHONY: dist
dist: main
	mkdir -p ../dist
	cp main ../dist/
	cp flag.txt ../dist/
	@echo "Distribution files copied to ../dist/"
