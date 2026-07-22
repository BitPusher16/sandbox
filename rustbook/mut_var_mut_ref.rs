// =====================================================
// RUST: Complete Educational Summary
// Ownership | Borrowing | Mutability | Lifetimes
// Run with rustc mut_var_mut_ref.rs.
// =====================================================

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

// Struct holding a reference (requires lifetime)
struct Excerpt<'a> {
    part: &'a str,           // Stores a reference to a string slice
}

// -----------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------

fn take_point(p: Point) {
    println!("  [take_point] Took ownership of: {:?}", p);
}

fn take_vec(v: Vec<i32>) {
    println!("  [take_vec] Took ownership of: {:?}", v);
}

fn print_point(p: &Point) {
    println!("  [print_point] Reading: {:?}", p);
}

fn print_vec(v: &Vec<i32>) {
    println!("  [print_vec] Reading: {:?}", v);
}

fn increment_point(p: &mut Point) {
    p.x += 1;
    p.y += 1;
}

fn push_value(v: &mut Vec<i32>) {
    v.push(999);
}

fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    println!("=== RUST OWNERSHIP, BORROWING, MUTABILITY & LIFETIMES ===\n");

    // =====================================================
    // SECTION 1: OWNED VALUES
    // =====================================================
    println!("--- 1. OWNED VALUES ---");

    let p = Point { x: 5, y: 10 };           // Immutable owned
    let mut mut_p = Point { x: 1, y: 2 };    // Mutable owned (can change fields)

    let v = vec![1, 2, 3];
    let mut mut_v = vec![10, 20];

    take_point(p);     // Moves ownership
    take_vec(v);       // Moves ownership

    // =====================================================
    // SECTION 2: IMMUTABLE BORROWS (&T)
    // =====================================================
    println!("\n--- 2. IMMUTABLE BORROWS (&T) ---");

    let owner = 42;
    let mut mut_owner = 42;

    // Immutable binding to immutable borrow
    let r1: &i32 = &owner;                   
    // Can read, but cannot rebind r1 or mutate data

    // Mutable binding to immutable borrow
    let mut r2: &i32 = &mut_owner;           
    // Can read + can rebind r2 to point somewhere else
    r2 = &owner;                             
    println!("  r2 (mutable binding to &T) can be reassigned");

    let point_ref: &Point = &mut_p;
    let vec_ref: &Vec<i32> = &mut_v;

    print_point(point_ref);
    print_vec(vec_ref);

    // =====================================================
    // SECTION 3: MUTABLE BORROWS (&mut T)
    // =====================================================
    println!("\n--- 3. MUTABLE BORROWS (&mut T) ---");

    let mut data = 100;
    let mut mut_point = Point { x: 1, y: 2 };
    let mut mut_vec = vec![1, 2];

    // Immutable binding to mutable borrow
    let mr1: &mut i32 = &mut data;           
    // Can mutate through mr1, but cannot rebind mr1 itself
    *mr1 = 200;

    // Mutable binding to mutable borrow
    let mut mr2: &mut i32 = &mut data;       
    // Can mutate + can rebind mr2 to another mutable reference
    mr2 = &mut data;
    *mr2 = 300;
    println!("  mr2 (mutable binding to &mut T) allows both mutation and rebinding");

    // Using mutable borrows with functions
    increment_point(&mut mut_point);
    push_value(&mut mut_vec);

    println!("  After mutation -> Point: {:?}", mut_point);
    println!("  After mutation -> Vec: {:?}", mut_vec);

    // =====================================================
    // SECTION 4: STRUCTS HOLDING REFERENCES
    // =====================================================
    println!("\n--- 4. STRUCTS HOLDING REFERENCES (Lifetime Required) ---");

    let text = String::from("Hello Rust lifetimes");
    let first = &text[..5];

    // The struct stores a reference, so it must declare a lifetime parameter.
    // This tells the compiler how long the stored reference is valid.
    let excerpt = Excerpt { part: first };
    println!("  Excerpt stored in struct: {}", excerpt.part);

    // =====================================================
    // SECTION 5: RETURNING REFERENCES
    // =====================================================
    println!("\n--- 5. RETURNING A REFERENCE (Requires Explicit Lifetime) ---");

    let s1 = String::from("This is a longer string");
    let s2 = String::from("short");

    // The 'a lifetime connects the inputs and output.
    // It guarantees the returned reference cannot outlive the data it points to.
    let result = longest(&s1, &s2);
    println!("  Longest: {}", result);
}
