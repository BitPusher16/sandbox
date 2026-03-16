use std::thread;
use std::time::Duration;

fn main(){
    loop{
        println!("+");
        thread::sleep(Duration::from_secs(1));
    }
}
