#include <stdio.h>
#define CROKEY_IMPL
#include "crokey.h"
#include <time.h>
#include <termios.h>
#include <unistd.h>

int main(int argc, char** argv){

	
	// disable terminal echo.
	struct termios term_curr, term_prev;
	tcgetattr(STDIN_FILENO, &term_prev);
	term_curr = term_prev;
	term_curr.c_lflag &= (~ICANON & ~ECHO);
	term_curr.c_cc[VMIN] = 1;
	term_curr.c_cc[VTIME] = 0;
	tcsetattr(STDIN_FILENO, TCSANOW, &term_curr);
	
	time_t time_curr;
	char char_last = KEY_LIST_NONE;
	char char_curr = '\n';
	while(1){
		time_curr = time(NULL);
		char_curr = crokey_get_pressed_key();

		if(char_curr != char_last){
			char_last = char_curr;
			if(char_curr != KEY_LIST_NONE){
				printf("%s %ld\n", crokey_enum_to_string(char_curr), (long)time_curr);
			}
		}
		

		if(char_curr == KEY_Q){
			break;
		}

	}

	// wait until key is released.
	while(crokey_get_pressed_key() != KEY_LIST_NONE){
		// wait
	}

	tcsetattr(STDIN_FILENO, TCSANOW, &term_prev);
	// what is difference between TCIFLUSH and TCAFLUSH?
	tcflush(STDIN_FILENO, TCIFLUSH); // this is required in case user held down q to exit.
	//tcflush(STDIN_FILENO, TCSAFLUSH); // this is required in case user held down q to exit.
	//fflush(stdin);
	//getchar();
	//printf("[press return to exit]\n");
	
	return 0;
}
