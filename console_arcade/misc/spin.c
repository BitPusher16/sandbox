#include <stdio.h>

int main(int argc, char** argv){
	long x = 0;
	for(long i = 0; i < 100000000000; i++){
		x += i;
	}
	return 0;
}
