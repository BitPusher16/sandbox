use std::io;
use std::time::Duration;
use std::time::Instant;

use crossterm::{execute, queue};
use crossterm::style::{Print, Stylize, Color, SetForegroundColor, ResetColor};
use std::io::{stdout, Write};

use crossterm::{
    event::{self, Event, KeyCode},
    terminal::{disable_raw_mode, enable_raw_mode},
};

fn main() -> io::Result<()> {
    enable_raw_mode()?;

    //let mut stdout = io::stdout();
    //let t_beg = Instant::now();
    //let t_tick_ms = 2000;
    //let mut t_rem = 
    //loop {
    //    if event::poll(Duration::from_millis(1200))? {
    //        // Read the event if available
    //        if let Event::Key(event) = event::read()? {
    //            //println!("Key pressed: {:?}\r", event.code);
    //            print!("Key pressed: {:?}\r\n", event.code);
    //            //stdout.write_all(b"Key pressed:\r\n")?;
    //            //execute!(stdout, Print("foo\r\n"))?;
    //            if event.code == KeyCode::Char('q') {
    //                //println!("Quitting...");
    //                break;
    //            }
    //        }
    //    } else {
    //        println!("No event available.\r\n");
    //    }
    //}

    let mut stdout = io::stdout();
    let tick_ms = Duration::from_millis(1000);
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
            let rem = tick_ms.as_millis() - (time_beg.elapsed().as_millis() % tick_ms.as_millis());
            remaining_ms = Duration::from_millis(rem as u64);
        }
    }

    disable_raw_mode()?;
    Ok(())
}
