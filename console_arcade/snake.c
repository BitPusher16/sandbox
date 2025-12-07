#include <stdio.h>
#include <time.h>
#include <termios.h>
#include <unistd.h>

#define CROKEY_IMPL
#include "crokey.h"

#ifndef MIN
#define MIN(a, b) (((a) < (b)) ? (a) : (b))
#endif

#ifndef MAX
#define MAX(a, b) (((a) > (b)) ? (a) : (b))
#endif

#ifndef CLAMP
/**
 * CLAMP: Clamps a value 'v' between a lower bound 'l' and an upper bound 'h' (inclusive).
 * The result will be at least 'l', and at most 'h'.
 */
#define CLAMP(v, l, h) MIN((h), MAX((v), (l)))
#endif


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

	int num_rows = 32;
	int num_cols = 32;
	int arry[num_rows][num_cols];

	//char chars[2] = {'X', '-'};

	//'\xe2\x96\x80'
	//'\xe2\x96\x84'
	//'\xe2\x96\x88'
	const char *upper = "\xe2\x96\x80";
	const char *lower = "\xe2\x96\x84";
	const char *both = "\xe2\x96\x88";
	const char *none = " ";

	char out[2000];
	int out_idx;

	int player_i = 1;
	int player_j = 1;

	time_t time_curr;
	//char char_prev = KEY_LIST_NONE;
	int char_curr = '\0';
	while(1){

		time_curr = time(NULL);
		char_curr = crokey_get_pressed_key();

		if(char_curr == KEY_J){ player_i += 1; }
		if(char_curr == KEY_K){ player_i -= 1; }
		if(char_curr == KEY_H){ player_j -= 1; }
		if(char_curr == KEY_L){ player_j += 1; }
		player_i = CLAMP(player_i, 1, num_rows-2);
		player_j = CLAMP(player_j, 1, num_cols-2);

		for(int i = 0; i < num_rows; i++){
			for(int j = 0; j < num_cols; j++){
				if(
					(i == player_i && j == player_j)
					|| i == 0
					|| i+1 == num_rows
					|| j == 0
					|| j+1 == num_cols
				){arry[i][j] = 1;}
				else{arry[i][j] = 0;}
			}
		}


		printf("\033[2J\033[1;1H"); // clear screen
		out_idx = 0;
		for(int i = 0; i < num_rows; i+= 2){
			for(int j = 0; j < num_cols; j++){

				//out[out_idx] = 'X';
				//out_idx++;


				if(arry[i][j] == 0 && arry[i+1][j] == 0){
					memcpy(out+out_idx, none, strlen(none));
					out_idx += strlen(none);
				}
				if(arry[i][j] == 0 && arry[i+1][j] == 1){
					memcpy(out+out_idx, lower, strlen(lower));
					out_idx += strlen(upper);
				}
				if(arry[i][j] == 1 && arry[i+1][j] == 0){
					memcpy(out+out_idx, upper, strlen(upper));
					out_idx += strlen(upper);
				}
				if(arry[i][j] == 1 && arry[i+1][j] == 1){
					memcpy(out+out_idx, both, strlen(both));
					out_idx += strlen(both);
				}

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
		usleep(50 * 1000);
		//sleep(1);
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
