#include <stdio.h>
#define CROKEY_IMPL
#include "crokey.h"
#include <time.h>
#include <termios.h>
#include <unistd.h>

int main(int argc, char** argv){

	//freopen("/dev/null", "r", stdin);
	
	// disable terminal echo.
	struct termios term_curr, term_prev;
	tcgetattr(STDIN_FILENO, &term_prev);
	term_curr = term_prev;
	term_curr.c_lflag &= ~ECHO;
	tcsetattr(STDIN_FILENO, TCSANOW, &term_curr);

	//printf("hello\n");
	time_t time_curr;
	char char_last = KEY_LIST_NONE;
	char char_curr = '\n';
	while(1){
		time_curr = time(NULL);
		char_curr = crokey_get_pressed_key();

		if(char_curr != char_last){
			char_last = char_curr;
			if(char_curr != KEY_LIST_NONE){
				//printf("%c\n", c);
				printf("%s %ld\n", crokey_enum_to_string(char_curr), (long)time_curr);
			}
		}
		

		if(char_curr == KEY_Q){
			break;
		}

	}

	// restore terminal echo
	tcsetattr(STDIN_FILENO, TCSANOW, &term_prev);
	return 0;
}
