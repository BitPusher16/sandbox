# https://codeberg.org/remoof/crokey

gcc snake.c -lX11

https://www.reddit.com/r/C_Programming/comments/v5k3z1/reading_char_for_char_from_stdin_without_waiting/

this person recommended using getchar() (linux only?)
https://stackoverflow.com/questions/7469139/what-is-the-equivalent-to-getch-getche-in-linux

2025-11-28
crokey causes cpu spin.
but i have discovered that getchar() does not cause spin, and can work as needed (no echo, no return) if terminal settings are updated as before.

switch away from crokey and use getchar()?
it may not be compatible with other platforms.

http://www.unixwiz.net/techtips/termios-vmin-vtime.html
VMIN > 0 and VTIME = 0
This is a counted read that is satisfied only when at least VMIN characters have been transferred to the caller's buffer - there is no timing component involved. This read can be satisfied from the driver's input queue (where the call could return immediately), or by waiting for new data to arrive: in this respect the call could block indefinitely. We believe that it's undefined behavior if nbytes is less then VMIN.

https://stackoverflow.com/questions/49684768/tcsetattr-what-are-the-differences-between-tcsanow-tcsadrain-tcsaflush-and
TCSAFLUSH — This is like TCSADRAIN, but also discards any queued input

realized something. the game loop needs to run, even if i am not providing input. so maybe i go back to using crokey? i can insert a sleep() call or something to prevent heavy cpu usage.

https://pubs.opengroup.org/onlinepubs/009696799/functions/tcflush.html
If queue_selector is TCIOFLUSH, it shall flush both data received but not read and data written but not transmitted
