#![warn(clippy::shadow_same)]
#![warn(clippy::shadow_reuse)]
#![warn(clippy::shadow_unrelated)]

use std::io;

fn main() {
    println!("Guess the number!");

    println!("Please input your guess.");
    let mut guess = String::new();
    io::stdin()
        .read_line(&mut guess)
        .expect("Failed to read line");

    println!("You guessed: {guess}");

    let apples = 5;
    let mut bananas = 7;

    let apples = apples + 1;

}
