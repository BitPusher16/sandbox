# This error appears if the pong.c file is not found:
# make: *** No rule to make target 'src/pong.c', needed by 'pong'.  Stop.
#
# https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html
# A phony target is one that is not really the name of a file; rather it is just a name for a recipe to be executed when you make an explicit request. There are two reasons to use a phony target: to avoid a conflict with a file of the same name, and to improve performance.
#
# In this example, the clean target will not work properly if a file named clean is ever created in this directory. Since it has no prerequisites, clean would always be considered up to date and its recipe would not be executed. To avoid this problem you can explicitly declare the target to be phony by making it a prerequisite of the special target .PHONY

# ========

# if user provides no argument to make, make runs the first target in the file.
.PHONY: run
run: pong
	./pong

# The following two lines mean: "Run gcc if 1) the file pong does not exist OR 2) src/pong.c has a modified-at date later than pong.
pong: src/pong.c
	gcc -g -O0 src/pong.c -o pong

.PHONY: clean
clean:
	rm -f pong.o
	rm -f pong

# this is only here so that make clean doesn't print # comments
# from lines in the rest of the file
.PHONY: end
end:
	echo hi

# ========

#.PHONY: run
#run: pong
	#./pong

#pong: src/pong.c
	#gcc src/pong.c -o pong

