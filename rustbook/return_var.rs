// =====================================================
// RUST RETURN TYPE PATTERNS - Complete Summary
// Ownership, Borrowing, and Lifetimes in Return Positions
// =====================================================

#[derive(Debug)]
struct Point { x: i32, y: i32 }

// -----------------------------------------------------
// 1. RETURNING OWNED VALUES (No lifetime needed)
// -----------------------------------------------------

// Returns a new owned value. Ownership is transferred to the caller.
fn create_point() -> Point {
    Point { x: 10, y: 20 }
}

// Returns an owned collection.
fn create_numbers() -> Vec<i32> {
    vec![1, 2, 3]
}

// -----------------------------------------------------
// 2. RETURNING IMMUTABLE REFERENCES (&T)
// -----------------------------------------------------

// Single input reference → Lifetime can be elided by the compiler.
fn get_first_char(s: &str) -> &str {
    &s[0..1]
}

// Multiple input references → Explicit lifetime is required.
// The returned reference lives as long as the shorter of the two inputs.
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// -----------------------------------------------------
// 3. RETURNING MUTABLE REFERENCES (&mut T)
// -----------------------------------------------------

// You can only return a &mut T if it comes from a mutable input.
// The returned reference is tied to the input's lifetime.
fn get_first_mut(v: &mut Vec<i32>) -> &mut i32 {
    &mut v[0]
}

// -----------------------------------------------------
// 4. RETURNING REFERENCES FROM STRUCTS (Methods)
// -----------------------------------------------------

impl Point {
    // Returns an immutable reference to a field
    fn get_x(&self) -> &i32 {
        &self.x
    }

    // Returns a mutable reference to a field
    fn get_x_mut(&mut self) -> &mut i32 {
        &mut self.x
    }

    // Returns owned value (takes ownership of self)
    fn into_tuple(self) -> (i32, i32) {
        (self.x, self.y)
    }
}

// -----------------------------------------------------
// 5. INVALID CASE: Returning reference to local data
// -----------------------------------------------------

// This function is INVALID and will not compile.
// You cannot return a reference to a value created inside the function.
/*
fn bad_return() -> &str {
    let s = String::from("hello");
    &s                    // ERROR: `s` is dropped at the end of the function
}
*/

fn main() {
    println!("=== RUST RETURN TYPE PATTERNS ===\n");

    // --- 1. Returning Owned Values ---
    let p = create_point();
    let nums = create_numbers();
    println!("Owned Point: {:?}", p);
    println!("Owned Vec: {:?}", nums);

    // --- 2. Returning Immutable References ---
    let text = String::from("Hello World");
    let first = get_first_char(&text);
    println!("First character: {}", first);

    let result = longest(&text, "short");
    println!("Longest string: {}", result);

    // --- 3. Returning Mutable References ---
    let mut numbers = vec![10, 20, 30];
    let first_mut = get_first_mut(&mut numbers);
    *first_mut = 99;                    // Mutate through the returned reference
    println!("After mutation: {:?}", numbers);

    // --- 4. Returning References via Methods ---
    let mut point = Point { x: 5, y: 10 };

    let x_ref = point.get_x();          // Immutable borrow via method
    println!("x via method: {}", x_ref);

    let x_mut = point.get_x_mut();      // Mutable borrow via method
    *x_mut = 42;
    println!("After mutating via method: {:?}", point);

    let tuple = point.into_tuple();     // Takes ownership of the Point
    println!("Converted to tuple: {:?}", tuple);
}
