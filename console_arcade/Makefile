CC = gcc
CFLAGS = -Wall -g
LDFLAGS = -lX11
TARGET = snake
SOURCES = snake.c
OBJECTS = $(SOURCES:.c=.o)

all: run

run: $(TARGET)
	./$(TARGET)

build: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJECTS)

