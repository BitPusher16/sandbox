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
	term_edit.c_cc[VMIN] = 1;
	term_edit.c_cc[VTIME] = 0;
	tcsetattr(STDIN_FILENO, TCSAFLUSH, &term_edit);

	// hide cursor;
	printf("\e[?25l");

	int num_rows = 10;
	int num_cols = 10;
	int arry[num_rows][num_cols];
	for(int i = 0; i < num_rows; i++){
		for(int j = 0; j < num_cols; j++){
			arry[i][j] = 0;
		}
	}

	char chars[2] = {'X', '-'};

	char out[200];
	int out_idx;

	time_t time_curr;
	char char_prev = KEY_LIST_NONE;
	int char_curr = '\0';
	while(1){
		out_idx = 0;
		time_curr = time(NULL);
		char_curr = crokey_get_pressed_key();
		printf("\033[2J\033[1;1H"); // clear screen

		for(int i = 0; i < num_rows; i+= 2){
			for(int j = 0; j < num_cols; j++){

				//out[out_idx] = 'X';
				//out_idx++;

				if(arry[i][j] == 0 && arry[i+1][j] == 0){out[out_idx] = '8';}
				if(arry[i][j] == 0 && arry[i+1][j] == 1){out[out_idx] = '°';}
				if(arry[i][j] == 1 && arry[i+1][j] == 0){out[out_idx] = 'o';}
				if(arry[i][j] == 1 && arry[i+1][j] == 1){out[out_idx] = ' ';}
				out_idx++;

				if(j+1 == num_cols){
					out[out_idx] = '\n';
					out_idx++;
				}
			}
		}

		out[out_idx] = '\0';
		printf("%s\n", out);


		//if(char_curr != char_prev){
		//	char_prev = char_curr;
		//	if(char_curr != KEY_LIST_NONE){
		//		printf("%s %ld\n", crokey_enum_to_string(char_curr), (long)time_curr);
		//	}
		//}
		printf("%s %ld\n", crokey_enum_to_string(char_curr), (long)time_curr);
		

		if(char_curr == KEY_Q){
			break;
		}
		//sleep(1);
		usleep(200);
	}

	// wait until quit key is released.
	while(crokey_get_pressed_key() != KEY_LIST_NONE){
		// wait
	}

	tcsetattr(STDIN_FILENO, TCSAFLUSH, &term_orig);
	tcflush(STDIN_FILENO, TCIOFLUSH);

	// show cursor
	printf("\e[?25h");
	
	return 0;
}
