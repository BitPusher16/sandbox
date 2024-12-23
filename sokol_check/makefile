# make will look for both "makefile" and "Makefile".
# $@ is the name of the file to be created.
# $? is the name(s) of the changed dependent(s)
# in a makefile, tabs are mandatory. spaces won't work.
# in a makefile, {} and () do the same thing. may prefer () to avoid ambiguity with bash vars.
# https://stackoverflow.com/questions/25185607/whats-the-difference-between-parenthesis-and-curly-bracket-syntax-in-ma
#
# if make receives no argument, it executes the first target in the file.

#herewith: hello.c linked_list.c
#	gcc hello.c

CC = gcc
INCLUDES = -I "."
#LIBS = "-lm"

#hello: hello.c
#	$(CC) $(INCLUDES) $? -o $@

#hello: hello.o linked_list.o linked_list.h
#	$(CC) $(INCLUDES) hello.o linked_list.o -o $@
#
#hello.o: hello.c linked_list.h
#	$(CC) -c $(INCLUDES) hello.c $@
#
#linked_list.o: linked_list.c linked_list.h
#	$(CC) -c $(INCLUDES) linked_list.c $@


hello: hello.o linked_list.o
	$(CC) $(INCLUDES) hello.o linked_list.o -o hello

hello.o: hello.c linked_list.h
	#$(CC) $(INCLUDES) hello.c -c hello.o # gives "linker input file unused" error
	$(CC) -c $(INCLUDES) hello.c -o hello.o

linked_list.o: linked_list.c linked_list.h
	#$(CC) $(INCLUDES) linked_list.c -c linked_list.o # gives "linker input file unused" error
	$(CC) -c $(INCLUDES) linked_list.c -o linked_list.o

clean:
	rm hello hello.o linked_list.o
