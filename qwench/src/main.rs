use std::io;
use std::io::{Write, Result};
use std::time::{Duration, Instant};

use crossterm::{execute, queue};
use crossterm::style::{Color, Colors, SetColors, ResetColor, Print};
use crossterm::cursor::{Hide, Show, MoveTo};
use crossterm::event::{self, Event, KeyCode};
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, size,
    BeginSynchronizedUpdate, EndSynchronizedUpdate, EnterAlternateScreen,
    LeaveAlternateScreen, DisableLineWrap, EnableLineWrap, Clear, ClearType,
};

const MIN_COLS: usize = 144;
const MIN_ROWS: usize = 48;

#[derive(Debug, Copy, Clone, PartialEq)]
struct CanvasCell {
    ch: char,
    fg: Color,
    bg: Color,
}

impl Default for CanvasCell{
    fn default() -> Self {
        Self {ch:'.', fg:Color::Blue, bg:Color::Black}
    }
}

//#[derive(Debug)]
//struct Canvas {
//    canvas: Vec<Vec<CanvasCell>>,
//}

type Canvas = Vec<Vec<CanvasCell>>;

//#[derive(Debug)]
//struct Sprite{
//    cells: Vec<Vec<CanvasCell>>,
//}

type Sprite = Vec<Vec<CanvasCell>>;

fn draw_onto(
    //a: &mut Vec<Vec<CanvasCell>>,
    canvas: &mut Canvas,
    //b: Vec<Vec<CanvasCell>>,
    sprite: Sprite,
    start_row: usize,
    start_col: usize,
) {
    let canv_m = canvas.len();
    if canv_m == 0 || sprite.is_empty() {
        return;
    }

    for (i, sprite_row) in sprite.iter().enumerate() {
        let target_row = start_row + i;
        if target_row >= canv_m { break; }

        let canv_row = &mut canvas[target_row];

        for (j, &cell) in sprite_row.iter().enumerate() {
            let target_col = start_col + j;
            if target_col >= canv_row.len() { break; }
            canv_row[target_col] = cell;
        }
    }
}

// call like:
//   let sprite = string_to_sprite(r#"
//       xbr $br zgr,
//       cbr xbr xbr,
//       xbr $br zgr,
//   "#);
fn string_to_sprite(input: &str) -> Sprite {
    fn char_to_color(c: char) -> Color {
        match c.to_ascii_lowercase() {
            'E' => Color::DarkGrey,
            'r' => Color::Red,
            'g' => Color::Green,
            'y' => Color::Yellow,
            'b' => Color::Blue,
            'm' => Color::Magenta,
            'c' => Color::Cyan,
            'w' => Color::White,
            'k' => Color::Black,
            'R' => Color::DarkRed,
            'G' => Color::DarkGreen,
            'Y' => Color::DarkYellow,
            'B' => Color::DarkBlue,
            'M' => Color::DarkMagenta,
            'C' => Color::DarkCyan,
            'e' => Color::Grey,
            _ => Color::Reset,
        }
    }

    let mut sprite: Sprite = Vec::new();
    let cleaned: String = input.chars().filter(|c| !c.is_whitespace()).collect();
    for row_str in cleaned.split(',') {
        if row_str.is_empty() { continue; }
        let chars: Vec<char> = row_str.chars().collect();
        let mut row = Vec::new();
        for i in (0..chars.len()).step_by(3) {
            if i + 2 >= chars.len() { break; }
            let ch = chars[i];
            let fg = char_to_color(chars[i + 1]);
            let bg = char_to_color(chars[i + 2]);
            row.push(CanvasCell { ch, fg, bg });
        }
        if !row.is_empty() { sprite.push(row); }
    }
    //Sprite { cells }
    sprite
}

#[derive(Debug, Copy, Clone)]
struct Raindrop { r: usize, c: usize, anim_state: i32, delete: bool }

#[derive(Debug, Copy, Clone)]
struct Cloud { r: usize, c: usize, anim_state: i32, delete: bool }

#[derive(Debug, Copy, Clone)]
struct Empty { r: usize, c: usize, anim_state: i32, delete: bool }

impl Raindrop {
    fn get_sprite(&self) -> Sprite {
        match self.anim_state {
            0 => string_to_sprite(r#"
                Owb Xwb Owb,
                Owb Orb Owb,
                Owb Orb Owb,
            "#),
            1 => string_to_sprite(r#"
                Owb Owb Owb,
                Owb Orb Owb,
                Owb Xwb Owb
            "#),
            _ => string_to_sprite(r#"Owb"#),
        }
    }

    fn update(&mut self) {
        self.anim_state = match self.anim_state {
            0 => 1,
            1 => 0,
            _ => self.anim_state
        }
    }
}

impl Cloud {
    fn get_sprite(&self) -> Sprite {
        match self.anim_state {
            0 => string_to_sprite(r#"
                vbw vbw vbw,
                vbw vbw vbw
            "#),
            1 => string_to_sprite(r#"
                ^bw ^bw ^bw,
                ^bw ^bw ^bw
            "#),
            _ => string_to_sprite(r#"-bw"#),
        }
    }

    fn update(&mut self) {
        self.anim_state = match self.anim_state {
            0 => 1,
            1 => 0,
            _ => self.anim_state
        }
    }
}

impl Empty {
    fn get_sprite(&self) -> Sprite {
        //string_to_sprite(r#" .bk "#)
        string_to_sprite(r#""#) // empty string has effect of making draw() do no-op.
    }

    fn update(&mut self) {
    }
}

#[derive(Debug, Copy, Clone)]
enum GridCell {
    Rd(Raindrop),
    Cd(Cloud),
    Em(Empty),
}

impl Default for GridCell{
    fn default() -> Self {
        GridCell::Em(Empty {r:0, c:0, anim_state:0, delete:false})
    }
}

trait GetSprite {
    fn get_sprite(&self) -> Sprite;
}

// implementing a trait on an enum allows us to do things like this:
//
//    // Build a mixed collection
//    let mixed: Vec<Thing> = vec![
//        Thing::Foo(Foo),
//        Thing::Bar(Bar),
//        Thing::Foo(Foo),
//        Thing::Bar(Bar),
//    ];
//
//    // Option A – static dispatch, but no extra helper needed
//    for item in &mixed {
//        item.bif();
//        println!("{:?}", item);
//    }
impl GetSprite for GridCell {
    fn get_sprite(&self) -> Sprite {
        match self {
            GridCell::Rd(rd) => rd.get_sprite(),
            GridCell::Cd(cd) => cd.get_sprite(),
            GridCell::Em(em) => em.get_sprite(),
        }
    }
}

trait Update {
    fn update(&mut self);
}

impl Update for GridCell {
    fn update(&mut self) {
        match self {
            GridCell::Rd(rd) => rd.update(),
            GridCell::Cd(cd) => cd.update(),
            GridCell::Em(em) => em.update(),
        }
    }
}

struct Game {
    out: Box<dyn Write>,
    //grid: Vec<Vec<Option<GridCell>>>,
    grid: Vec<Vec<GridCell>>,
    //next_grid: Vec<Vec<GridCell>>,
    update_applied: Vec<Vec<bool>>,
    canvas: Vec<Vec<CanvasCell>>,
    elts_updated: u32,
}

impl Game{
    fn new(m: usize, n: usize, out: Box<dyn Write>) -> Self{
        Game {
            out,
            //grid: vec![vec![None; n]; m],
            //grid: vec![vec![GridCell.default(); n]; m],
            grid: vec![vec![GridCell::default(); n]; m],
            //next_grid: vec![vec![GridCell::default(); n]; m],
            update_applied: vec![vec![false; n]; m],
            canvas: vec![vec![CanvasCell::default(); n]; m],
            elts_updated: 0,
        }
    }

    fn update(&mut self) {
        for row in &mut self.update_applied { row.fill(false); }

        let (m, n) = (self.grid.len(), self.grid[0].len());
        for i in 0..m {
            for j in 0..n {
                ////if let Some(mut elt) = self.grid[i][j] {  // hm, yuck... this makes a copy.
                ////if let Some(ref mut elt) = self.grid[i][j] {  // also works.
                //if let Some(elt) = &mut self.grid[i][j] {  // works.
                //    elt.update(); 
                //    self.elts_updated += 1;
                //}

                // if we have already finalized this cell (possibly while examining previous cell),
                // do nothing.
                if self.update_applied[i][j]{ continue; }

                self.update_applied[i][j] = true;
                self.grid[i][j].update();

                // piece interaction logic.
                match self.grid[i][j] {
                    GridCell::Rd(rd) => {
                        if i + 1 == m{
                            self.grid[i][j] = GridCell::default();
                        }
                        else{
                            // if raindrop is above cloud, remove it.
                            if matches!(self.grid[i + 1][j], GridCell::Cd(_)){
                                self.grid[i][j] = GridCell::default();
                            }
                            else{
                                self.grid[i+1][j] = self.grid[i][j];
                                self.grid[i][j] = GridCell::default();
                                // we have moved raindrop into next cell down,
                                // so we should not update it again.
                                self.update_applied[i+1][j] = true;
                            }
                        }
                    }
                    GridCell::Cd(cd) => {
                    }
                    GridCell::Em(em) => {
                    }
                }
            }
        }
    }

    fn draw(&mut self) -> Result<()> {
        for row in self.canvas.iter_mut(){
            row.fill(CanvasCell::default());
        }

        // copy object sprites to canvas.
        let (m, n) = (self.grid.len(), self.grid[0].len());
        for i in 0..m {
            for j in 0..n {
                //if let Some(elt) = self.grid[i][j] { 
                //    let sprite = elt.get_sprite();
                //    draw_onto(&mut self.canvas, sprite, i, j);
                //}
                let sprite = self.grid[i][j].get_sprite();
                draw_onto(&mut self.canvas, sprite, i, j);
            }
        }

        let (curr_cols, curr_rows) = size()?;
        let curr_cols = curr_cols as usize;
        let curr_rows = curr_rows as usize;
        if curr_rows < m || curr_cols < n {
            execute!(self.out, Clear(ClearType::All), MoveTo(0,0))?;
            queue!(self.out, Print(format!(
                "game dims set to {} rows, {} cols, current terminal dims are {} rows, {} cols.", 
                m, MIN_COLS, curr_rows, curr_cols)))?;
            self.out.flush()?;
        }
        else{
            // we will center the game grid in the available terminal space.
            let top_left_r = (curr_rows - m) / 2;
            let top_left_c = (curr_cols - n) / 2;

            queue!(self.out, BeginSynchronizedUpdate)?;
            queue!(self.out, Clear(ClearType::All))?;

            // simple optimization to reduce writes to stdout:
            // only print color change chars when necessary.
            let mut last_colors = None;

            for i in 0..m {
                queue!(self.out, MoveTo(top_left_c as u16, (top_left_r + i) as u16))?;
                for j in 0..n {
                    let colors = Colors::new(self.canvas[i][j].fg, self.canvas[i][j].bg);
                    if Some(colors) != last_colors {
                        queue!(self.out, SetColors(colors))?;
                        last_colors = Some(colors);
                    }
                    queue!(self.out, Print(self.canvas[i][j].ch))?;
                }
            }

            // prepare to write out any post-grid contents.
            execute!(self.out, ResetColor)?;
            queue!(self.out, MoveTo(top_left_c as u16, (top_left_r + m) as u16))?;

            // print score, timer here?

            queue!(self.out, EndSynchronizedUpdate)?;
            self.out.flush()?;
        }
        Ok(())
    }

    fn set_up(&mut self) -> Result<()>{
        enable_raw_mode()?;
        execute!(self.out, EnterAlternateScreen, Hide, DisableLineWrap)?;
        self.out.flush()?;
        Ok(())
    }

    fn tear_down(&mut self) -> Result<()>{
        disable_raw_mode()?;
        execute!(self.out, LeaveAlternateScreen, Show, EnableLineWrap,)?;
        self.out.flush()?;
        println!("elts updated: {}", self.elts_updated);
        Ok(())
    }

    fn game_loop(&mut self) -> Result<()>{

        // add some objects for debugging.
        //self.grid[2][2] = Some(GridCell::Rd(Raindrop{r:0, c:0, anim_state:1, delete:false}));
        //self.grid[8][8] = Some(GridCell::Cd(Cloud{r:0, c:0, anim_state:0, delete:false}));

        self.grid[2][2] = GridCell::Rd(Raindrop{r:0, c:0, anim_state:1, delete:false});
        self.grid[8][8] = GridCell::Cd(Cloud{r:0, c:0, anim_state:0, delete:false});
        self.grid[16][2] = GridCell::Cd(Cloud{r:0, c:0, anim_state:0, delete:false});

        let tick_dur = Duration::from_millis(200);
        let time_beg = Instant::now();
        let mut quit = false;
        let mut remaining_dur = tick_dur;

        //let mut key_presses = 0;

        while !quit {
            if event::poll(remaining_dur)? {
                if let Event::Key(event) = event::read()? {
                    // \r is required because in raw mode the cursor doesn't automatically return.
                    print!("Key pressed: {:?}\r\n", event.code);
                    //key_presses += 1;
                    if event.code == KeyCode::Char('q') {
                        quit = true;
                    }
                }
                // as_millis() returns a u128, but from_millis() requires a u64.
                let rem = tick_dur.as_millis() - (time_beg.elapsed().as_millis() % tick_dur.as_millis());
                remaining_dur = Duration::from_millis(rem as u64);
            }
            else{
                self.update();
                self.draw()?;

                let rem = tick_dur.as_millis() - (time_beg.elapsed().as_millis() % tick_dur.as_millis());
                remaining_dur = Duration::from_millis(rem as u64);
            }
        }
        Ok(())
    }

    fn run(&mut self) -> Result<()> {
        self.set_up()?;
        self.game_loop()?;
        self.tear_down()?;
        Ok(())
    }
}

fn main() -> Result<()> {
    // TODO: parse command line args.
    
    let rows = MIN_ROWS;
    let cols = MIN_COLS;
    let mut game = Game::new(rows, cols, Box::new(io::stdout()));
    game.run()?;
    Ok(())
}
