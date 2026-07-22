-- This module serves as the root of the `LeanIntro` library.
-- Import modules here that should be built as part of the library.
import LeanIntro.Basic

/- Define some constants. -/

def m : Nat := 1       -- m is a natural number
def n : Nat := 0
def b1 : Bool := true  -- b1 is a Boolean
def b2 : Bool := false

#check m
#check n
#check n + 0
#check m * (n + 0)
#check b1-- "&&" is the Boolean and
#check b1 && b2-- Boolean or
#check b1 || b2-- Boolean "true"
#check true/- Evaluate -/

#eval 5 * 4
#eval m + 2
#eval b1 && b2



#check Nat → Nat
#check Nat -> Nat
#check Nat × Nat
#check Prod Nat Nat
#check Nat → Nat → Nat
#check Nat → (Nat → Nat)
#check Nat × Nat → Nat
#check (Nat → Nat) → Nat


