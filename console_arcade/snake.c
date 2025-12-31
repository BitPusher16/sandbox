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

// clamp inclusive.
#ifndef CLAMP
#define CLAMP(v, l, h) MIN((h), MAX((v), (l)))
#endif

enum direction{ UP, DN, LT, RT, NL };

struct pair {
	int i;
	int j;
};

typedef struct pair pair;

int main(int argc, char** argv){

	// disable terminal canonical mode (terminate input on newline) and echo.
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
	int board[num_rows][num_cols];

	int m_n = num_rows * num_cols;
	pair snake[m_n];
	snake[0].i = 2;
	snake[0].j = 2;
	snake[1].i = 2;
	snake[1].j = 3;
	snake[2].i = 2;
	snake[2].j = 4;
	int snake_beg = 0;
	int snake_end = 2;

	const char *upper = "\xe2\x96\x80";
	const char *lower = "\xe2\x96\x84";
	const char *both = "\xe2\x96\x88";
	const char *none = " ";

	char out[num_rows * num_cols + 1024];
	int out_idx;

	// player location must match snake head as instantiated.
	int player_i = 2;
	int player_j = 4;
	int tail_i = 2;
	int tail_j = 2;
	enum direction curr;

	// populate walls.
	for(int i = 0; i < num_rows; i++){
		for(int j = 0; j < num_cols; j++){
			if(
				i == 0
				|| i+1 == num_rows
				|| j == 0
				|| j+1 == num_cols
			){board[i][j] = 1;}
			else{board[i][j] = 0;}
		}
	}

	time_t time_curr;
	//char char_prev = KEY_LIST_NONE;
	int char_curr = '\0';
	while(1){

		time_curr = time(NULL);

		// capture input.
		char_curr = crokey_get_pressed_key();

		curr = NL; // null
		if(char_curr == KEY_S){ curr = DN; } // down
		if(char_curr == KEY_W){ curr = UP; } // up
		if(char_curr == KEY_A){ curr = LT; } // left
		if(char_curr == KEY_D){ curr = RT; } // right

		// update state.
		board[player_i][player_j] = 0;
		if(curr == UP){ player_i -= 1; }
		if(curr == DN){ player_i += 1; }
		if(curr == LT){ player_j -= 1; }
		if(curr == RT){ player_j += 1; }
		
		player_i = CLAMP(player_i, 1, num_rows-2);
		player_j = CLAMP(player_j, 1, num_cols-2);
		board[player_i][player_j] = 1;

		if(curr != NL){
			// add next snake element.
			// append at right side (snake_end).
			snake_end += 1;
			snake_end %= m_n;
			snake[snake_end].i = player_i;
			snake[snake_end].j = player_j;

			// remove last snake element.
			// before removing, save a copy so it can be erased later.
			tail_i = snake[snake_beg].i;
			tail_j = snake[snake_beg].j;
			snake_beg += 1;
			snake_beg %= m_n;
		}


		// draw snake to board.
		int k;
		k = snake_beg;
		while(k != snake_end){
			board[snake[k].i][snake[k].j] = 1;
			k += 1;
			k %= m_n;
		}
		// one last iteration.
		board[snake[k].i][snake[k].j] = 1;
		k += 1;
		k %= m_n;

		// erase snake tail.
		board[tail_i][tail_j] = 0;

		// render.
		printf("\033[2J\033[1;1H"); // clear screen
		out_idx = 0;
		for(int i = 0; i < num_rows; i+= 2){
			for(int j = 0; j < num_cols; j++){

				//out[out_idx] = 'X';
				//out_idx++;

				if(board[i][j] == 0 && board[i+1][j] == 0){
					memcpy(out+out_idx, none, strlen(none));
					out_idx += strlen(none);
				}
				if(board[i][j] == 0 && board[i+1][j] == 1){
					memcpy(out+out_idx, lower, strlen(lower));
					out_idx += strlen(upper);
				}
				if(board[i][j] == 1 && board[i+1][j] == 0){
					memcpy(out+out_idx, upper, strlen(upper));
					out_idx += strlen(upper);
				}
				if(board[i][j] == 1 && board[i+1][j] == 1){
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
	}

	// wait until quit key is released.
	while(crokey_get_pressed_key() != KEY_LIST_NONE){
		// spin.
	}

	// restore terminal attributes.
	tcsetattr(STDIN_FILENO, TCSAFLUSH, &term_orig);
	tcflush(STDIN_FILENO, TCIOFLUSH);

	// show cursor
	printf("\e[?25h");
	
	return 0;
}
