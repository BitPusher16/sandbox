-- https://lean-lang.org/functional_programming_in_lean/#

-- https://lean-lang.org/functional_programming_in_lean/Getting-to-Know-Lean/Evaluating-Expressions/#evaluating
-- "In Lean, programs are first and foremost expressions, and the primary way to think about computation 
-- is as evaluating expressions to find their values."

#eval 1 + 2

#eval String.append "Hello, " "Lean!"

-- https://lean-lang.org/functional_programming_in_lean/Getting-to-Know-Lean/Types/#getting-to-know-types
-- "every expression must have a type before it can be evaluated"

def add1 (n : Nat) : Nat := n + 1

#eval add1 7

def maximum (n : Nat) (k : Nat) : Nat :=
  if n < k then
    k
  else
    n

#eval maximum (5 + 8) (2 * 7)
#check maximum (5 + 8) (2 * 7)
#check String.append "Goodby, " "Lean"

-- https://lean-lang.org/functional_programming_in_lean/Getting-to-Know-Lean/Functions-and-Definitions/#functions-and-definitions
-- "a function that accepts two Nats and returns a Nat has type Nat → Nat → Nat.
-- As a special case, Lean returns a function's signature when its name is used directly with #check. 
-- Entering #check add1 yields add1 (n : Nat) : Nat. 
-- However, Lean can be “tricked” into showing the function's type by writing the function's name in parentheses, 
-- which causes the function to be treated as an ordinary expression"

#check add1
#check (add1)

#check maximum
#check (maximum)

-- "Function arrows associate to the right, which means that Nat → Nat → Nat should be parenthesized Nat → (Nat → Nat)."

def joinStringsWith (s1 : String) (s2 : String) (s3: String) := String.append s2 (String.append s1 s3)
#eval joinStringsWith ", " "one" "and another"

def volume (l : Nat) (w : Nat) (h : Nat) := l * w * h
#eval volume 2 3 4


-- what does it mean that "In Lean, types are a first-class part of the language"?

-- "In Lean, however, types are a first-class part of the language—they are expressions like any other. 
-- This means that definitions can refer to types just as well as they can refer to other values."

-- since types are expressions, does that mean they can be evaluated? how do you evaluate (rewrite to a simpler form) a type?

-- "Types are expressions, and in an expression, a defined name can be replaced with its definition."

-- two looming questions:
-- what does it mean for types to be first-class members of the language?
-- what are dependent types and why are they important?

def NaturalNumber : Type := Nat
--def thirtyEight : NaturalNumber := 38 -- why error here?
-- because literals (like 38) can also be names, and lean does not substitute Nat in for Natural number
-- before it tries to evaluate NaturalNumber := 38, so it cannot infer that 38 is a natural number and not a name.

def thirtyEight : NaturalNumber := (38 : Nat) -- no error

-- alternatively, use abbrev, which is always replaced.
-- internally, definitions produced with abbrev are marked as *reducible*.
abbrev NaturalNoomber : Type := Nat
def thirtyNine : NaturalNoomber := 39

structure Point where
  x : Float
  y : Float

def origin : Point := { x := 0.0, y := 0 } -- y type Float is inferred!

#eval origin
#eval origin.x
#eval origin.y

-- stopped before completing the exercises here:
-- https://lean-lang.org/functional_programming_in_lean/Getting-to-Know-Lean/Structures/#structures













