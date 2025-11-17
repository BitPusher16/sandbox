#include <stdio.h>
#define CROKEY_IMPL
#include "crokey.h"
#include <time.h>
#include <termios.h>
#include <unistd.h>

#define ERASE_LINE "\033[2K\r"

int main(int argc, char** argv){

	//struct termios orig_termios;

	//void die(const char *s) {
	//    perror(s);
	//    exit(1);
	//}

	//void disable_raw_mode() {
	//    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios) == -1) {
	//	die("tcsetattr");
	//    }
	//}

	//void enable_raw_mode() {
	//    if (tcgetattr(STDIN_FILENO, &orig_termios) == -1) {
	//	die("tcgetattr");
	//    }
	//    atexit(disable_raw_mode);  // Restore on exit

	//    struct termios raw = orig_termios;
	//    raw.c_lflag &= ~(ICANON | ECHO);  // Disable canonical mode and echo
	//    raw.c_cc[VMIN] = 1;  // Read at least 1 byte
	//    raw.c_cc[VTIME] = 0; // No timeout

	//    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) {
	//	die("tcsetattr");
	//    }
	//}

	//freopen("/dev/null", "r", stdin);
	
	// disable terminal echo.
	struct termios term_curr, term_prev;
	tcgetattr(STDIN_FILENO, &term_prev);
	term_curr = term_prev;
	//term_curr.c_lflag &= ~ECHO;
	term_curr.c_lflag &= (~ICANON & ~ECHO);
	term_curr.c_cc[VMIN] = 1;
	term_curr.c_cc[VTIME] = 0;
	tcsetattr(STDIN_FILENO, TCSANOW, &term_curr);
	
	//enable_raw_mode();

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
				//printf("\r\033[K"); // clear line
				printf(ERASE_LINE);
				printf("%s %ld\n", crokey_enum_to_string(char_curr), (long)time_curr);
			}
		}
		

		if(char_curr == KEY_Q){
		//if(char_curr == KEY_ESCAPE){
			break;
		}

	}

	// restore terminal echo
	sleep(1); // give time for user to release 'q' key;
	tcsetattr(STDIN_FILENO, TCSANOW, &term_prev);

	// ??
	//scanf("%*[^\n]");
	
	//fseek(stdin, 0, SEEK_END);
	
	//char c;
	//while(c = getchar());
	
	//for(int i = 0; i < 1000; i++){
	//	write(STDOUT_FILENO, "\b \b", 3);
	//}
	
	//fflush(stdin);
	tcflush(STDIN_FILENO, TCIFLUSH); // this is required to prevent writing of keys at program exit.
	
	return 0;
}
