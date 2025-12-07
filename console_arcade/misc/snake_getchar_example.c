#include <stdio.h>
#include <time.h>
#include <termios.h>
#include <unistd.h>

int main(int argc, char** argv){
	
	// disable terminal canonical mode (input newline termination) and echo.
	struct termios term_edit, term_orig;
	tcgetattr(STDIN_FILENO, &term_orig);
	term_edit = term_orig;
	term_edit.c_lflag &= (~ICANON & ~ECHO);
	term_edit.c_cc[VMIN] = 1;
	term_edit.c_cc[VTIME] = 0;
	tcsetattr(STDIN_FILENO, TCSAFLUSH, &term_edit);

	time_t time_curr;
	char c;
	while(1){
		time_curr = time(NULL);
		char c = getchar();
		printf("\033[2J\033[1;1H");
		//printf("[2J\033[1;1H");
		printf("-%c\n", c);
		if(c == 'q'){break;}
	}


	tcsetattr(STDIN_FILENO, TCSANOW, &term_orig);
	// what is difference between TCIFLUSH and TCAFLUSH?
	//tcflush(STDIN_FILENO, TCIFLUSH); // this is required in case user held down q to exit.
	//tcflush(STDIN_FILENO, TCSAFLUSH); // this is required in case user held down q to exit.
	//fflush(stdin);
	//getchar();
	//printf("[press return to exit]\n");
	
	return 0;
}
