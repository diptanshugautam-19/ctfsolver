CC = gcc
CFLAGS = -fno-stack-protector -no-pie -z execstack -Wl,-z,relro -Wl,-z,now
TARGET = quantum_memory

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $(TARGET) main.c

clean:
	rm -f $(TARGET)

.PHONY: all clean
