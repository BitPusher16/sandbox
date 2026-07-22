#![allow(warnings)]

// =====================================================
// RUST: Ownership & Borrowing Reference Sheet
// Cleaned Up Version
// =====================================================

use std::collections::HashMap;

fn main() {
    // =====================================================
    // PART 1: VARIABLE DECLARATIONS
    // =====================================================

    println!("=== Part 1: Variable Declarations ===\n");

    // --- i32 ---
    let owned_i32: i32 = 42;
    let mut mut_owned_i32: i32 = 42;

    let r_i32: &i32 = &owned_i32;
    let mut mut_r_i32: &i32 = &owned_i32;

    let mut_ref_i32: &mut i32 = &mut mut_owned_i32;           // Immutable binding + &mut T
    *mut_ref_i32 += 1;

    let mut mut_mut_ref_i32: &mut i32 = &mut mut_owned_i32;   // Mutable binding + &mut T
    *mut_mut_ref_i32 += 1;

    // --- Vec<i32> ---
    let owned_vec: Vec<i32> = vec![1, 2, 3];
    let mut mut_owned_vec: Vec<i32> = vec![10, 20];

    let r_vec: &Vec<i32> = &owned_vec;
    let mut mut_r_vec: &Vec<i32> = &owned_vec;

    let mut_ref_vec: &mut Vec<i32> = &mut mut_owned_vec;
    mut_ref_vec.push(100);

    let mut mut_mut_ref_vec: &mut Vec<i32> = &mut mut_owned_vec;
    mut_mut_ref_vec.push(200);

    // --- HashMap ---
    let owned_map: HashMap<String, i32> = HashMap::new();
    let mut mut_owned_map: HashMap<String, i32> = HashMap::new();

    let r_map: &HashMap<String, i32> = &owned_map;
    let mut mut_r_map: &HashMap<String, i32> = &owned_map;

    let mut_ref_map: &mut HashMap<String, i32> = &mut mut_owned_map;
    mut_ref_map.insert("a".to_string(), 1);

    let mut mut_mut_ref_map: &mut HashMap<String, i32> = &mut mut_owned_map;
    mut_mut_ref_map.insert("b".to_string(), 2);

    // =====================================================
    // PART 2: DEMONSTRATIONS
    // =====================================================

    println!("=== Part 2: Demonstrations ===\n");

    println!("Reading values:");
    println!("  owned_i32 = {}", owned_i32);
    println!("  r_i32     = {}", r_i32);
    println!("  mut_r_i32 = {}", mut_r_i32);

    // Rebinding (only works with mutable bindings)
    mut_r_i32 = &owned_i32;
    mut_r_vec = &owned_vec;
    mut_r_map = &owned_map;

    println!("\nRebinding mutable bindings successful.");

    // =====================================================
    // PART 3: PASSING TO FUNCTIONS
    // =====================================================

    println!("\n=== Part 3: Passing to Functions ===");

    read_i32(&owned_i32);
    read_vec(&owned_vec);
    read_map(&owned_map);

    modify_i32(&mut mut_owned_i32);
    modify_vec(&mut mut_owned_vec);
    modify_map(&mut mut_owned_map);

    take_i32(owned_i32);      // move
    take_vec(owned_vec);      // move
    take_map(owned_map);      // move

    // =====================================================
    // PART 4: RETURNING FROM FUNCTIONS
    // =====================================================

    println!("\n=== Part 4: Returning from Functions ===");

    let new_i32 = make_i32();
    let new_vec = make_vec();
    let new_map = make_map();

    let ref_i32 = get_ref_i32(&new_i32);
    let ref_vec = get_ref_vec(&new_vec);
    let ref_map = get_ref_map(&new_map);

    println!("Returned references created successfully.");
}

// =====================================================
// HELPER FUNCTIONS
// =====================================================

fn read_i32(x: &i32)                    { println!("  read_i32: {}", x); }
fn read_vec(v: &Vec<i32>)               { println!("  read_vec"); }
fn read_map(m: &HashMap<String, i32>)   { println!("  read_map"); }

fn modify_i32(x: &mut i32)              { *x += 1; }
fn modify_vec(v: &mut Vec<i32>)         { v.push(0); }
fn modify_map(m: &mut HashMap<String, i32>) { m.insert("updated".to_string(), 1); }

fn take_i32(x: i32)                     { println!("  take_i32"); }
fn take_vec(v: Vec<i32>)                { println!("  take_vec"); }
fn take_map(m: HashMap<String, i32>)    { println!("  take_map"); }

fn make_i32() -> i32                    { 42 }
fn make_vec() -> Vec<i32>               { vec![1, 2, 3] }
fn make_map() -> HashMap<String, i32>   { HashMap::new() }

fn get_ref_i32(x: &i32) -> &i32         { x }
fn get_ref_vec(v: &Vec<i32>) -> &Vec<i32> { v }
fn get_ref_map(m: &HashMap<String, i32>) -> &HashMap<String, i32> { m }
