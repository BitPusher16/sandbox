#include <stdio.h>
#include <time.h>
#include <termios.h>
#include <unistd.h>

#define CROKEY_IMPL
#include "crokey.h"

int main(int argc, char** argv){
	
	// disable terminal canonical mode (input newline termination) and echo.
	struct termios term_edit, term_orig;
	tcgetattr(STDIN_FILENO, &term_orig);
	term_edit = term_orig;
	term_edit.c_lflag &= (~ICANON & ~ECHO);
	//term_edit.c_cc[VMIN] = 1;
	//term_edit.c_cc[VTIME] = 0;
	//tcsetattr(STDIN_FILENO, TCSANOW, &term_edit);
	tcsetattr(STDIN_FILENO, TCSAFLUSH, &term_edit);

	//char c = getchar();
	//printf("--\n");
	//c = getchar();
	
	time_t time_curr;
	char char_prev = KEY_LIST_NONE;
	char char_curr = '\n';
	while(1){
		char discard = getchar(); // this 
		printf("captured with getchar: %c\n", discard);
		time_curr = time(NULL);
		char_curr = crokey_get_pressed_key();

		if(char_curr != char_prev){
			char_prev = char_curr;
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

	tcsetattr(STDIN_FILENO, TCSANOW, &term_orig);
	// what is difference between TCIFLUSH and TCAFLUSH?
	tcflush(STDIN_FILENO, TCIFLUSH); // this is required in case user held down q to exit.
	//tcflush(STDIN_FILENO, TCSAFLUSH); // this is required in case user held down q to exit.
	//fflush(stdin);
	//getchar();
	//printf("[press return to exit]\n");
	
	return 0;
}
