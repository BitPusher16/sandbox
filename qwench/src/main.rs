/* 
 * read command line args. grid size, word list, char list, rate of word generation.
 * init game structs. (grids, word lists, etc.)
 * init console.
 * game loop.
 *   verify that console has sufficient rows, cols.
 *   if key press:
 *     determine if key is valid.
 *     if valid, redraw only affected chars.
 *   if game tick:
 *     update grid. (place new words, move rain, move fire, update score.)
 *     draw grid.
 * restore console.
 *
 *
 */

use std::io;
use std::io::{Write, Result};
use std::env;
use std::time::{Duration, Instant};

use crossterm::style::{Color, Colors, SetColors, ResetColor, Print};
use crossterm::cursor::{Hide, Show, MoveTo};
use crossterm::event::{self, Event, KeyCode};
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, BeginSynchronizedUpdate, EndSynchronizedUpdate, EnterAlternateScreen,
    LeaveAlternateScreen, DisableLineWrap, EnableLineWrap, Clear, ClearType, size,
};
use crossterm::{execute, queue};

#[derive(Clone, Copy, PartialEq)]
struct Cell {
    ch: char,
    fg: Color,
    bg: Color,
}

/*
 * there are 176-32=144 printable ascii chars not counting space.
 * show statistics after every game.
 * support a flag that allows appending single game statistics to file.
 */

const MIN_COLS: usize = 144;
const MIN_ROWS: usize = 48;

fn draw(grid: &[Vec<Cell>], stdout: &mut impl Write, top_left_r: usize, top_left_c: usize) -> io::Result<()>{
    let top_left_r = top_left_r as u16;
    let top_left_c = top_left_c as u16;

    queue!(stdout, BeginSynchronizedUpdate)?;
    queue!(stdout, Clear(ClearType::All))?;
    //queue!(stdout, MoveTo(top_left_c, top_left_r))?;
    let mut last_colors = None;
    for(y, row) in grid.iter().enumerate(){
        let y = y as u16;
        queue!(stdout, MoveTo(top_left_c, top_left_r + y))?;
        for(x, cell) in row.iter().enumerate(){
            let x = x as u16;
            let colors = Colors::new(cell.fg, cell.bg);
            if Some(colors) != last_colors {
                queue!(stdout, SetColors(colors))?;
                last_colors = Some(colors);
            }
            queue!(stdout, Print(cell.ch))?;
        }
        //queue!(stdout, Print("\r\n"))?;
    }
    execute!(stdout, ResetColor)?;
    let grid_len = grid.len() as u16;
    queue!(stdout, MoveTo(top_left_c, top_left_r + grid_len))?;
    queue!(stdout, EndSynchronizedUpdate)?;
    stdout.flush()
}

fn main() -> Result<()> {

    let args: Vec<String> = env::args().collect();

    if args.len() != 3 {
        eprintln!("Usage: {} <rows> <cols>", args[0]);
        std::process::exit(1);
    }
    
    // Parse the two numbers (rows and columns)
    let rows: usize = args[1].parse().expect("first argument (rows) must be a positive integer.");
    let cols: usize = args[2].parse().expect("second argument (cols) must be a positive integer.");

    if rows < MIN_ROWS { print!("rows must be at least {}.\n", MIN_ROWS); return Ok(()); }
    if cols < MIN_COLS { print!("cols must be at least {}.\n", MIN_COLS); return Ok(()); }

    let mut grid: Vec<Vec<Cell>> = vec![vec![
        Cell{ch:' ', fg:Color::Blue, bg:Color::DarkGrey}
    ; cols as usize]; rows as usize];

    for i in 0..rows{
        for j in 0..cols{
            if i == 0 || j == 0 || i+1 == rows || j+1 == cols{
                grid[i][j].ch = 'X';
            }
        }
    }

    let mut stdout = io::stdout();
    enable_raw_mode()?;
    execute!( stdout, EnterAlternateScreen, Hide, DisableLineWrap)?;

    let tick_ms = Duration::from_millis(200);
    let time_beg = Instant::now();
    let mut quit = false;
    let mut remaining_ms = tick_ms;

    while !quit {
        if event::poll(remaining_ms)? {
            if let Event::Key(event) = event::read()? {
                // \r is required because in raw mode the cursor doesn't automatically return.
                print!("Key pressed: {:?}\r\n", event.code);
                if event.code == KeyCode::Char('q') {
                    quit = true;
                }
            }
            // as_millis() returns a u128, but from_millis() requires a u64.
            let rem = tick_ms.as_millis() - (time_beg.elapsed().as_millis() % tick_ms.as_millis());
            remaining_ms = Duration::from_millis(rem as u64);
        }
        else{
            print!("drawing...\r\n");
            let (curr_cols, curr_rows) = size()?;
            let curr_cols = curr_cols as usize;
            let curr_rows = curr_rows as usize;
            if(curr_rows < rows || curr_cols < cols){
                execute!(stdout, Clear(ClearType::All), MoveTo(0,0))?;
                queue!(stdout, Print(format!("min terminal dims are {} rows, {} cols, curr dims are {}, {}", MIN_ROWS, MIN_COLS, curr_rows, curr_cols)))?;
                stdout.flush()?;
            }
            else{
                let top_left_r = (curr_rows - rows) / 2;
                let top_left_c = (curr_cols - cols) / 2;
                draw(&grid, &mut stdout, top_left_r, top_left_c)?;
            }

            //execute!(stdout, Clear(ClearType::All), MoveTo(0,0))?;
            //stdout.flush()?;

            let rem = tick_ms.as_millis() - (time_beg.elapsed().as_millis() % tick_ms.as_millis());
            remaining_ms = Duration::from_millis(rem as u64);
        }
    }

    disable_raw_mode()?;
    execute!( stdout, LeaveAlternateScreen, Show, EnableLineWrap,)?;
    stdout.flush()?;

    //println!("Press ENTER to continue...");
    //let mut buffer = String::new();
    //io::stdout().flush().expect("Failed to flush stdout"); // Ensures the message is displayed immediately
    //io::stdin().read_line(&mut buffer).expect("Failed to read line");
    //println!("Continuing execution...");

    Ok(())
}

