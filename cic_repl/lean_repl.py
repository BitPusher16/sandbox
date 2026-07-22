"""
lean_repl.py  —  A minimal Lean-like dependent type theory kernel + REPL

ARCHITECTURE OVERVIEW
=====================
This file implements a small fragment of the Calculus of Inductive
Constructions (CIC) that underlies Lean 4.  The goal is clarity over
completeness: every design choice mirrors Lean, but only the pieces
needed to state and prove simple theorems about the natural numbers
are included.

UNIVERSE HIERARCHY (mirroring Lean)
=====================================
Lean's universe hierarchy:

    Sort 0  ≡  Prop          -- the universe of propositions
    Sort 1  ≡  Type 0        -- the universe of "ordinary" data types
    Sort 2  ≡  Type 1        -- the universe of types whose elements are types
    Sort n  ≡  Type (n-1)    -- in general

In Lean you write `Type` as shorthand for `Type 0`.
`Sort 0` (Prop) is special: it is *impredicative* — a forall whose
codomain lives in Prop also lives in Prop, regardless of the domain.
This is what lets us write ∀ (P Q : Prop), P → Q → P without leaving Prop.

We represent universes as:
    Sort(0)               — Prop
    Sort(1)               — Type 0  (written `Type` in Lean)
    Sort(n) for n >= 1   — Type (n-1)
"""

from __future__ import annotations
from typing import override
import sys
import re
from dataclasses import dataclass
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# 1.  TERM REPRESENTATION
#     Every syntactic object in the type theory is a Term.
# ──────────────────────────────────────────────────────────────────────────────

class Term:
    """Abstract base for all terms."""
    pass


@dataclass
class Sort(Term):
    """
    Sort(level)

    Sort(0) = Prop   — universe of propositions (impredicative)
    Sort(1) = Type   — universe of small data types  (= Type 0 in Lean)
    Sort(n) = Type (n-1)

    In Lean:  `Prop : Type 1`, and `Type n : Type (n+1)`.
    Here we capture that by saying Sort(n) : Sort(n+1).
    """
    level: int

    @override
    def __repr__(self):
        if self.level == 0:
            return "Prop"
        return f"Type {self.level - 1}" if self.level > 1 else "Type"


@dataclass
class Var(Term):
    """A free or bound variable, referred to by name."""
    name: str

    @override
    def __repr__(self):
        return self.name


@dataclass
class App(Term):
    """Function application:  (func arg)"""
    func: Term
    arg: Term

    @override
    def __repr__(self):
        f = f"({self.func})" if isinstance(self.func, (Lam, Pi)) else repr(self.func)
        a = f"({self.arg})" if isinstance(self.arg, (App, Lam, Pi)) else repr(self.arg)
        return f"{f} {a}"


@dataclass
class Lam(Term):
    """
    Lambda abstraction:  fun (x : A) => body
    This is the *proof term* / *function* constructor.
    In Lean 4 syntax:  `fun x : A => body`
    """
    var: str
    var_type: Term
    body: Term

    @override
    def __repr__(self):
        return f"fun ({self.var} : {self.var_type}) => {self.body}"


@dataclass
class Pi(Term):
    """
    Dependent product (forall / function type):
        (x : A) → B

    When x does not appear free in B this is just A → B.
    When the codomain B lives in Sort(0)=Prop this is a *proposition*.

    In Lean 4 syntax:
        ∀ (x : A), B       — when B : Prop
        (x : A) → B        — general arrow type
    """
    var: str
    var_type: Term
    body: Term

    @override
    def __repr__(self):
        if not free_in(self.var, self.body):
            return f"{_paren_if(self.var_type)} → {self.body}"
        return f"∀ ({self.var} : {self.var_type}), {self.body}"


@dataclass
class NatLit(Term):
    """A natural number literal — syntactic sugar for Nat.zero / Nat.succ."""
    value: int

    @override
    def __repr__(self):
        return str(self.value)


@dataclass
class Const(Term):
    """
    A global constant declared in the environment.
    Examples: Nat, Nat.zero, Nat.succ, Nat.rec, Eq, Eq.refl, …
    """
    name: str

    @override
    def __repr__(self):
        return self.name


# ──────────────────────────────────────────────────────────────────────────────
# 2.  SUBSTITUTION AND FREE-VARIABLE HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def free_in(name: str, term: Term) -> bool:
    """Return True if `name` appears free in `term`."""
    match term:
        case Sort(_):           return False
        case Const(_):          return False
        case NatLit(_):         return False
        case Var(n):            return n == name
        case App(f, a):         return free_in(name, f) or free_in(name, a)
        case Lam(v, vt, b):     return free_in(name, vt) or (v != name and free_in(name, b))
        case Pi(v, vt, b):      return free_in(name, vt) or (v != name and free_in(name, b))
        case _:                 return False


def subst(name: str, replacement: Term, term: Term) -> Term:
    """
    Capture-avoiding substitution: replace free occurrences of `name`
    with `replacement` inside `term`.
    """
    match term:
        case Sort(_) | Const(_) | NatLit(_):
            return term
        case Var(n):
            return replacement if n == name else term
        case App(f, a):
            return App(subst(name, replacement, f), subst(name, replacement, a))
        case Lam(v, vt, b):
            new_vt = subst(name, replacement, vt)
            if v == name:
                return Lam(v, new_vt, b)          # shadowed — don't touch body
            if free_in(v, replacement):            # alpha-rename to avoid capture
                fresh = _fresh(v, b, replacement)
                b = subst(v, Var(fresh), b)
                v = fresh
            return Lam(v, new_vt, subst(name, replacement, b))
        case Pi(v, vt, b):
            new_vt = subst(name, replacement, vt)
            if v == name:
                return Pi(v, new_vt, b)
            if free_in(v, replacement):
                fresh = _fresh(v, b, replacement)
                b = subst(v, Var(fresh), b)
                v = fresh
            return Pi(v, new_vt, subst(name, replacement, b))
        case _:
            return term


_fresh_counter = 0

def _fresh(base: str, *terms: Term) -> str:
    global _fresh_counter
    _fresh_counter += 1
    return f"{base}_{_fresh_counter}"

def _paren_if(t: Term) -> str:
    if isinstance(t, (Pi, Lam)):
        return f"({t})"
    return repr(t)


# ──────────────────────────────────────────────────────────────────────────────
# 3.  ENVIRONMENT  (global declaration store)
#     In Lean this is the "environment" Γ — a map from names to
#     (type, optional definition).
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Declaration:
    """
    A global declaration.  Either:
      • An *axiom* / *opaque constant*: has a type but no definition body.
      • A *definition* / *theorem*: has both a type and a proof/definition term.
    """
    name: str
    type: Term
    value: Optional[Term] = None     # None → axiom/opaque
    is_inductive: bool = False       # True → generated by `inductive`


class Environment:
    def __init__(self):
        self.decls: dict[str, Declaration] = {}

    def add(self, decl: Declaration):
        if decl.name in self.decls:
            raise KernelError(f"'{decl.name}' is already declared")
        self.decls[decl.name] = decl

    def lookup(self, name: str) -> Declaration:
        if name not in self.decls:
            raise KernelError(f"unknown identifier '{name}'")
        return self.decls[name]

    def has(self, name: str) -> bool:
        return name in self.decls


class KernelError(Exception):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# 4.  REDUCTION / NORMALISATION
#     The kernel must decide when two terms are *definitionally equal*.
#     We implement weak-head normal form (whnf) reduction plus full
#     normalisation for display purposes.
#
#     Reduction rules IMPLEMENTED:
#       β  :  (fun x => body) arg  ↦  body[x := arg]
#             The core computation rule for functions.  Every proof that
#             applies a lambda to an argument uses this.
#
#       δ  :  unfold transparent definitions from the environment.
#             Nat.add, Nat.mul, double, etc. are unfolded so the kernel
#             can see through them when checking definitional equality.
#             Inductive type constants (Nat, Eq, …) are NOT unfolded (opaque).
#
#       ι  :  (iota) recursor/eliminator reduction for inductive types.
#             Nat.rec base step Nat.zero          ↦  base
#             Nat.rec base step (Nat.succ n)      ↦  step n (Nat.rec base step n)
#             This is what makes arithmetic compute: 2 + 3 reduces to 5
#             by repeated ι-steps.
#
#     Reduction rules OMITTED (not needed for Nat + Prop proofs):
#
#       ζ  :  (zeta) local let-binding unfolding.
#             In Lean:  let x := e; body  ↦  body[x := e]
#             This is just β for a syntactic sugar — "let x := e in body"
#             is sugar for (fun x => body) e, so β already covers it.
#             We omit "let" syntax entirely; if added, zeta would be a
#             one-liner in whnf alongside the Var/Const δ cases.
#
#       η  :  (eta) function extensionality for the kernel equality check.
#             η says:   f  ≡  fun x => f x   (when x not free in f)
#             We DO implement η in def_eq (see _def_eq_whnf, the Lam cases
#             that expand one side), so eta-equality is checked.  What we
#             omit is η-*reduction* as a rewrite rule inside whnf — Lean's
#             kernel also does not reduce η eagerly; it only checks it during
#             definitional equality comparison, exactly as we do.
#
#       quot:  quotient type reduction -- IMPLEMENTED in section 4b below.
# ──────────────────────────────────────────────────────────────────────────────

def whnf(env: Environment, ctx: dict[str, Term], term: Term) -> Term:
    """Reduce `term` to weak-head normal form."""
    while True:
        match term:
            case Var(n):
                if n in ctx:
                    return term   # local variable — keep as-is
                # Not local — check if it's a global definition
                if env.has(n):
                    decl = env.lookup(n)
                    if decl.value is not None and not decl.is_inductive:
                        term = decl.value
                        continue
                    return Const(n)   # opaque global constant
                return term

            case Const(n):
                decl = env.lookup(n)
                if decl.value is not None and not decl.is_inductive:
                    term = decl.value   # δ-reduction: unfold definition
                    continue
                return term

            case App(func, arg):
                func_whnf = whnf(env, ctx, func)
                match func_whnf:
                    case Lam(v, _, body):
                        # β-reduction
                        term = subst(v, arg, body)
                        continue
                    case _:
                        # Try ι-reduction for recursors
                        #result = try_iota(env, ctx, func_whnf, arg)
                        #if result is not None:
                        #    term = result
                        #    continue
                        # collect all arguments for multi-arg ι
                        result2 = try_iota_multiarg(env, ctx, App(func_whnf, arg))
                        if result2 is not None:
                            term = result2
                            continue
                        return App(func_whnf, arg)

            case NatLit(n):
                # Expand to Nat.zero / Nat.succ ... for recursor reduction
                return nat_lit_to_term(n)

            case _:
                return term


#def try_iota(env: Environment, ctx: dict[str, Term], func: Term, arg: Term) -> Optional[Term]:
#    """
#    Single-step ι-reduction attempt: func is in whnf, arg is next argument.
#    We handle Nat.rec here.
#    """
#    return None   # handled in try_iota_multiarg


def try_iota_multiarg(env: Environment, ctx: dict[str, Term], app: Term) -> Optional[Term]:
    """
    Collect the spine of an application and check if the head is a recursor
    whose major premise is in constructor form.

    Nat.rec : {motive : Nat → Sort u} →
              motive Nat.zero →
              ((n : Nat) → motive n → motive (Nat.succ n)) →
              (t : Nat) →
              motive t

    Application order: Nat.rec motive base step major
    """
    head, spine = collect_spine(app)

    if isinstance(head, Const) and head.name == "Nat.rec":
        # spine = [motive, base, step, major]  (motive may be implicit — we skip it)
        # We support both 3-arg (base, step, major) and 4-arg (motive, base, step, major)
        if len(spine) >= 3:
            if len(spine) == 3:
                base_term, step_term, major = spine
            else:
                # motive + base + step + major (+ possible extra apps)
                base_term, step_term, major = spine[-3], spine[-2], spine[-1]
                extra = spine[len(spine):]  # nothing extra in len==4 case

            major_whnf = whnf(env, ctx, major)
            # Check for Nat.zero
            if isinstance(major_whnf, Const) and major_whnf.name == "Nat.zero":
                result = base_term
                # re-apply any extra spine beyond the 4 core args
                for ex in spine[4:]:
                    result = App(result, ex)
                return result
            # Check for Nat.succ n
            if isinstance(major_whnf, App):
                hd2, sp2 = collect_spine(major_whnf)
                if isinstance(hd2, Const) and hd2.name == "Nat.succ" and len(sp2) == 1:
                    pred = sp2[0]
                    # step pred (Nat.rec base step pred)
                    rec_pred = App(App(App(Const("Nat.rec"), base_term), step_term), pred)
                    result = App(App(step_term, pred), rec_pred)
                    for ex in spine[4:]:
                        result = App(result, ex)
                    return result
    # ── Bool.rec ι-reduction ─────────────────────────────────────────────
    #
    # inductive Bool : Type where | false | true
    #
    # Bool.rec : (motive : Bool → Sort u) →
    #            motive Bool.false →
    #            motive Bool.true  →
    #            (b : Bool) → motive b
    #
    # Reduction rules:
    #   Bool.rec motive fval tval Bool.false  ↦  fval
    #   Bool.rec motive fval tval Bool.true   ↦  tval
    #
    # This is the if/then/else of dependent type theory.  When motive is
    # a constant type (fun _ => T), Bool.rec is exactly an if-expression:
    #   Bool.rec (fun _ => T) e_false e_true b  ≡  if b then e_true else e_false
    # (Note: Bool.false branch comes first in the recursor, matching the
    #  zero/succ convention: false=0, true=1.)
    if isinstance(head, (Const, Var)) and head.name in ("Bool.rec", "Bool.casesOn"):
        # spine = [motive, fval, tval, major]  — exactly 4 args required.
        # Bool.rec takes motive + 2 branches + 1 major = 4.
        # Do NOT fire with fewer args or we mistake a partial application
        # (motive, fval, tval) for (fval, tval, major).
        if len(spine) >= 4:
            fval  = spine[-3]   # branch for Bool.false
            tval  = spine[-2]   # branch for Bool.true
            major = spine[-1]
            major_whnf = whnf(env, ctx, major)
            name2 = major_whnf.name if isinstance(major_whnf, (Const, Var)) else None
            if name2 == "Bool.false":
                result = fval
                for ex in spine[len(spine):]:
                    result = App(result, ex)
                return result
            if name2 == "Bool.true":
                result = tval
                for ex in spine[len(spine):]:
                    result = App(result, ex)
                return result

    # ── Quot.lift reduction (quot-reduction / quot-beta) ──────────────────
    quot_result = try_quot_reduction(env, ctx, app)
    if quot_result is not None:
        return quot_result

    return None


def collect_spine(term: Term) -> tuple[Term, list[Term]]:
    """Decompose (((f a) b) c) into (f, [a, b, c])."""
    spine = []
    while isinstance(term, App):
        spine.append(term.arg)
        term = term.func
    spine.reverse()
    return term, spine


def nat_lit_to_term(n: int) -> Term:
    """Convert integer n to its Nat representation using Nat.zero and Nat.succ."""
    t: Term = Const("Nat.zero")
    for _ in range(n):
        t = App(Const("Nat.succ"), t)
    return t



# ──────────────────────────────────────────────────────────────────────────────
# 4b. QUOTIENT TYPE REDUCTION
#
# Lean's quotient types are axiomatic primitives.  The four constants:
#
#   Quot      : (a:Type) -> (a->a->Prop) -> Type             -- type former
#   Quot.mk   : (a:Type) -> (r:a->a->Prop) -> a -> Quot a r  -- constructor
#   Quot.lift : (a b:Type) -> (r:a->a->Prop) ->              -- eliminator
#               (f:a->b) -> (forall x y, r x y -> Eq b (f x) (f y)) ->
#               Quot a r -> b
#   Quot.ind  : ... -> (forall a, P (Quot.mk r a)) -> forall q, P q
#
# Plus the axiom (no reduction rule):
#   Quot.sound: r a b -> Eq (Quot r) (Quot.mk r a) (Quot.mk r b)
#
# The reduction rule (quot-beta):
#
#   Quot.lift r f h (Quot.mk r a)  ->  f a
#
# This fires when Quot.lift's major premise reduces to a Quot.mk.
# The soundness proof h is discarded (it was only needed to ensure
# the lift is well-defined for arbitrary elements of the quotient).
#
# Why this is central: unlike Nat.rec whose rule is an instance of the
# general scheme for inductive eliminators, Quot.lift's rule is a new
# axiom added to the kernel.  Lean's kernel has exactly four reduction
# rules: beta, delta, iota (inductives), and quot.  The standard
# library's integers, rationals, and real numbers all rest on this.
# ──────────────────────────────────────────────────────────────────────────────

def try_quot_reduction(env: "Environment", ctx: dict[str, Term], app: Term) -> Optional[Term]:
    """
    quot-beta: Quot.lift alpha beta r f h (Quot.mk alpha r a)  ->  f a

    We look for Quot.lift at the head of the application spine, then check
    whether the final argument (the major premise) is a Quot.mk.
    Spine layout (explicit form):
      head = Quot.lift,  spine = [alpha, beta, r, f, h, major]
    We index from the end so implicit args do not need to be counted exactly.
    """
    head, spine = collect_spine(app)
    name = head.name if isinstance(head, (Const, Var)) else None
    if name != "Quot.lift":
        return None
    # Need at least: f, h, major  (3 trailing args)
    if len(spine) < 3:
        return None

    major = spine[-1]
    major_whnf = whnf(env, ctx, major)

    hd2, sp2 = collect_spine(major_whnf)
    mk_name = hd2.name if isinstance(hd2, (Const, Var)) else None
    if mk_name != "Quot.mk":
        return None
    # sp2 = [alpha, r, a]  or [r, a] -- the representative is always last
    if len(sp2) < 1:
        return None
    a = sp2[-1]

    # f is spine[-3]: Quot.lift ... r f h major
    f = spine[-3]
    return App(f, a)


def normalize(env: Environment, ctx: dict[str, Term], term: Term) -> Term:
    """Fully normalise a term (for display)."""
    wh = whnf(env, ctx, term)
    match wh:
        case Sort(_) | Var(_): return wh
        case NatLit(_): return wh
        case Const(n) if n == "Nat.zero":  return NatLit(0)     # display as 0
        case Const(n) if n == "Bool.true":  return Const("true")   # display as true
        case Const(n) if n == "Bool.false": return Const("false")  # display as false
        case Const(_): return wh
        case App(f, a):
            nf = App(normalize(env, ctx, f), normalize(env, ctx, a))
            # Try to collapse to NatLit for pretty display
            return try_collapse_nat(env, nf)
        case Lam(v, vt, b):
            return Lam(v, normalize(env, ctx, vt), normalize(env, ctx, b))
        case Pi(v, vt, b):
            return Pi(v, normalize(env, ctx, vt), normalize(env, ctx, b))
        case _: return wh


def try_collapse_nat(env: Environment, term: Term) -> Term:
    """If term is a chain of Nat.succ ... Nat.zero, collapse to NatLit."""
    n = 0
    t = term
    while True:
        if isinstance(t, Const) and t.name == "Nat.zero":
            return NatLit(n)
        if isinstance(t, NatLit):
            return NatLit(n + t.value)   # e.g. Nat.succ (NatLit 1) -> NatLit 2
        if isinstance(t, App):
            h, sp = collect_spine(t)
            if isinstance(h, Const) and h.name == "Nat.succ" and len(sp) == 1:
                n += 1
                t = sp[0]
                continue
        return term  # not a nat chain


# ──────────────────────────────────────────────────────────────────────────────
# 5.  TYPE CHECKER
#     Implements bidirectional type checking for CIC.
#     infer(env, ctx, term) → type
#     check(env, ctx, term, expected_type) → (verified)
# ──────────────────────────────────────────────────────────────────────────────

def infer(env: Environment, ctx: dict[str, Term], term: Term) -> Term:
    """
    Infer the type of `term` in context `ctx`.
    ctx maps variable names → their types.
    """
    match term:

        # ── Universe typing ──────────────────────────────────────────────────
        case Sort(n):
            # Sort(n) : Sort(n+1)
            # So: Prop : Type,  Type : Type 1,  etc.
            return Sort(n + 1)

        # ── Variables ────────────────────────────────────────────────────────
        case Var(name):
            if name in ctx:
                return ctx[name]
            # Not a local variable — try the global environment (acts like Const)
            if env.has(name):
                return env.lookup(name).type
            raise KernelError(f"unbound variable '{name}'")

        # ── Global constants ─────────────────────────────────────────────────
        case Const(name):
            return env.lookup(name).type

        # ── Natural number literals ───────────────────────────────────────────
        case NatLit(_):
            return Const("Nat")

        # ── Application ──────────────────────────────────────────────────────
        case App(func, arg):
            func_type = infer(env, ctx, func)
            func_type_wh = whnf(env, ctx, func_type)
            if not isinstance(func_type_wh, Pi):
                raise KernelError(
                    f"expected a function type, got {normalize(env, ctx, func_type)}\n"
                    + f"  when applying {func} to {arg}"
                )
            check(env, ctx, arg, func_type_wh.var_type)
            return subst(func_type_wh.var, arg, func_type_wh.body)

        # ── Lambda ───────────────────────────────────────────────────────────
        case Lam(v, vt, body):
            # Check that vt is a valid type (lives in some Sort)
            vt_sort = infer(env, ctx, vt)
            _ = ensure_sort(env, ctx, vt_sort)
            new_ctx = {**ctx, v: vt}
            body_type = infer(env, new_ctx, body)
            return Pi(v, vt, body_type)

        # ── Pi (forall / arrow) ───────────────────────────────────────────────
        case Pi(v, vt, body):
            vt_sort = infer(env, ctx, vt)
            s1 = ensure_sort(env, ctx, vt_sort)
            new_ctx = {**ctx, v: vt}
            body_sort_term = infer(env, new_ctx, body)
            s2 = ensure_sort(env, new_ctx, body_sort_term)
            return pi_sort(s1, s2)

        case _:
            raise KernelError(f"cannot infer type of {term!r}")


def check(env: Environment, ctx: dict[str, Term], term: Term, expected: Term):
    """
    Check that `term` has type `expected`.
    We use definitional equality (def_eq) to compare.
    """
    actual = infer(env, ctx, term)
    if not def_eq(env, ctx, actual, expected):
        raise KernelError(
            f"type mismatch\n"
            + f"  term     : {term}\n"
            + f"  expected : {normalize(env, ctx, expected)}\n"
            + f"  got      : {normalize(env, ctx, actual)}"
        )


def ensure_sort(env: Environment, ctx: dict[str, Term], t: Term) -> int:
    """Reduce t to a Sort and return its level.  Raises if not a sort."""
    wh = whnf(env, ctx, t)
    if isinstance(wh, Sort):
        return wh.level
    raise KernelError(f"expected a Sort, got {normalize(env, ctx, t)}")


def pi_sort(s1: int, s2: int) -> Sort:
    """
    Universe rule for Pi types (the 'rule' of the PTS):
       (Sort s1, Sort s2) → Sort ?

    Lean's rules:
      • If s2 == 0 (Prop): result is Prop  ← impredicativity of Prop
      • Otherwise: result is Sort(max(s1, s2))

    This is what makes `∀ (P : Prop), P → P` live in Prop even though
    P ranges over all propositions.
    """
    if s2 == 0:
        return Sort(0)   # Prop is impredicative
    return Sort(max(s1, s2))


def def_eq(env: Environment, ctx: dict[str, Term], t1: Term, t2: Term) -> bool:
    """
    Definitional equality: are t1 and t2 equal up to reduction?
    We normalise both and compare structurally.
    """
    n1 = whnf(env, ctx, t1)
    n2 = whnf(env, ctx, t2)
    return _def_eq_whnf(env, ctx, n1, n2)


def _def_eq_whnf(env: Environment, ctx: dict[str, Term], t1: Term, t2: Term) -> bool:
    match (t1, t2):
        case (Sort(a), Sort(b)):            return a == b
        case (Var(a), Var(b)):              return a == b
        case (Const(a), Const(b)):          return a == b
        case (Var(a), Const(b)):            return a == b
        case (Const(a), Var(b)):            return a == b
        case (NatLit(a), NatLit(b)):        return a == b
        case (NatLit(_), _):
            return _def_eq_whnf(env, ctx, nat_lit_to_term(t1.value), t2)
        case (_, NatLit(_)):
            return _def_eq_whnf(env, ctx, t1, nat_lit_to_term(t2.value))
        case (App(f1, a1), App(f2, a2)):
            return (_def_eq_whnf(env, ctx, f1, f2) and
                    def_eq(env, ctx, a1, a2))
        case (Pi(v1, vt1, b1), Pi(v2, vt2, b2)):
            if not def_eq(env, ctx, vt1, vt2):
                return False
            # rename v2 → v1 in b2
            b2r = subst(v2, Var(v1), b2)
            new_ctx = {**ctx, v1: vt1}
            return def_eq(env, new_ctx, b1, b2r)
        case (Lam(v1, vt1, b1), Lam(v2, vt2, b2)):
            if not def_eq(env, ctx, vt1, vt2):
                return False
            b2r = subst(v2, Var(v1), b2)
            new_ctx = {**ctx, v1: vt1}
            return def_eq(env, new_ctx, b1, b2r)
        # η-expansion: f =?= fun x => f x
        case (Lam(v, vt, b), _):
            new_ctx = {**ctx, v: vt}
            return def_eq(env, new_ctx, b, App(t2, Var(v)))
        case (_, Lam(v, vt, b)):
            new_ctx = {**ctx, v: vt}
            return def_eq(env, new_ctx, App(t1, Var(v)), b)
        case _:
            return False


# ──────────────────────────────────────────────────────────────────────────────
# 6.  BUILT-IN DECLARATIONS
#     We pre-populate the environment with the things Lean provides:
#       • Nat and its constructors / recursor
#       • Eq and its constructor / recursor
#       • Basic logical connectives (And, Or, Not, Iff, True, False)
# ──────────────────────────────────────────────────────────────────────────────

def build_initial_env() -> Environment:
    env = Environment()

    # ── Nat ──────────────────────────────────────────────────────────────────
    # inductive Nat : Type where
    #   | zero : Nat
    #   | succ : Nat → Nat
    env.add(Declaration("Nat", Sort(1), is_inductive=True))
    env.add(Declaration("Nat.zero", Const("Nat")))
    env.add(Declaration("Nat.succ", Pi("n", Const("Nat"), Const("Nat"))))

    # Nat.rec (the recursor — the *only* elimination principle for Nat)
    #
    # Nat.rec : {motive : Nat → Sort u} →
    #            motive Nat.zero →
    #            ((n : Nat) → motive n → motive (Nat.succ n)) →
    #            (t : Nat) →
    #            motive t
    #
    # We give a simplified type that works for Sort 0 and Sort 1 by
    # making motive's Sort implicit. The kernel's ι-rule does the real work.
    Nat_rec_type = Pi(
        "motive", Pi("_", Const("Nat"), Sort(1)),   # motive : Nat → Type
        Pi(
            "base", App(Var("motive"), Const("Nat.zero")),
            Pi(
                "step", Pi("n", Const("Nat"),
                           Pi("ih", App(Var("motive"), Var("n")),
                              App(Var("motive"), App(Const("Nat.succ"), Var("n"))))),
                Pi(
                    "t", Const("Nat"),
                    App(Var("motive"), Var("t"))
                )
            )
        )
    )
    env.add(Declaration("Nat.rec", Nat_rec_type, is_inductive=True))

    # ── Eq ───────────────────────────────────────────────────────────────────
    # inductive Eq : {α : Sort u} → α → α → Prop where
    #   | refl : ∀ (a : α), Eq a a
    #
    # Eq α a b : Prop
    # Eq.refl : ∀ {α : Type} (a : α), Eq a a

    # Eq : {α : Type} → α → α → Prop
    Eq_type = Pi("α", Sort(1),
                 Pi("a", Var("α"),
                    Pi("b", Var("α"), Sort(0))))
    env.add(Declaration("Eq", Eq_type, is_inductive=True))

    # Eq.refl : ∀ {α : Type} (a : α), Eq α a a
    Eq_refl_type = Pi("α", Sort(1),
                      Pi("a", Var("α"),
                         App(App(App(Const("Eq"), Var("α")), Var("a")), Var("a"))))
    env.add(Declaration("Eq.refl", Eq_refl_type))

    # Eq.subst (substitution / transport):
    # Eq.subst : ∀ {α : Type} {motive : α → Prop} {a b : α},
    #              Eq α a b → motive a → motive b
    Eq_subst_type = Pi("α", Sort(1),
                    Pi("motive", Pi("_", Var("α"), Sort(0)),
                    Pi("a", Var("α"),
                    Pi("b", Var("α"),
                    Pi("h", App(App(App(Const("Eq"), Var("α")), Var("a")), Var("b")),
                    Pi("ma", App(Var("motive"), Var("a")),
                       App(Var("motive"), Var("b"))))))))
    env.add(Declaration("Eq.subst", Eq_subst_type))

    # Eq.symm : ∀ {α : Type} {a b : α}, Eq α a b → Eq α b a
    Eq_symm_type = Pi("α", Sort(1),
                   Pi("a", Var("α"),
                   Pi("b", Var("α"),
                   Pi("h", App(App(App(Const("Eq"), Var("α")), Var("a")), Var("b")),
                      App(App(App(Const("Eq"), Var("α")), Var("b")), Var("a"))))))
    env.add(Declaration("Eq.symm", Eq_symm_type))

    # Eq.trans : ∀ {α : Type} {a b c : α}, Eq α a b → Eq α b c → Eq α a c
    Eq_trans_type = Pi("α", Sort(1),
                    Pi("a", Var("α"),
                    Pi("b", Var("α"),
                    Pi("c", Var("α"),
                    Pi("h1", App(App(App(Const("Eq"), Var("α")), Var("a")), Var("b")),
                    Pi("h2", App(App(App(Const("Eq"), Var("α")), Var("b")), Var("c")),
                       App(App(App(Const("Eq"), Var("α")), Var("a")), Var("c"))))))))
    env.add(Declaration("Eq.trans", Eq_trans_type))

    # ── Propositional connectives ─────────────────────────────────────────────
    # These mirror Lean's Prop-level types exactly.

    # True : Prop          (the trivially-true proposition)
    # True.intro : True
    env.add(Declaration("True", Sort(0)))
    env.add(Declaration("True.intro", Const("True")))

    # False : Prop         (the empty proposition — has no proof)
    # False.elim : ∀ {C : Prop}, False → C
    env.add(Declaration("False", Sort(0)))
    False_elim_type = Pi("C", Sort(0), Pi("h", Const("False"), Var("C")))
    env.add(Declaration("False.elim", False_elim_type))

    # Not (P : Prop) : Prop  :=  P → False
    Not_type = Pi("P", Sort(0), Sort(0))
    Not_def  = Lam("P", Sort(0), Pi("_", Var("P"), Const("False")))
    env.add(Declaration("Not", Not_type, Not_def))

    # And (P Q : Prop) : Prop
    # And.intro : P → Q → And P Q
    # And.left  : And P Q → P
    # And.right : And P Q → Q
    And_type = Pi("P", Sort(0), Pi("Q", Sort(0), Sort(0)))
    env.add(Declaration("And", And_type, is_inductive=True))
    And_intro_type = Pi("P", Sort(0),
                     Pi("Q", Sort(0),
                     Pi("p", Var("P"),
                     Pi("q", Var("Q"),
                        App(App(Const("And"), Var("P")), Var("Q"))))))
    env.add(Declaration("And.intro", And_intro_type))
    And_left_type = Pi("P", Sort(0),
                    Pi("Q", Sort(0),
                    Pi("h", App(App(Const("And"), Var("P")), Var("Q")),
                       Var("P"))))
    env.add(Declaration("And.left", And_left_type))
    And_right_type = Pi("P", Sort(0),
                     Pi("Q", Sort(0),
                     Pi("h", App(App(Const("And"), Var("P")), Var("Q")),
                        Var("Q"))))
    env.add(Declaration("And.right", And_right_type))

    # Or (P Q : Prop) : Prop
    # Or.inl : P → Or P Q
    # Or.inr : Q → Or P Q
    Or_type = Pi("P", Sort(0), Pi("Q", Sort(0), Sort(0)))
    env.add(Declaration("Or", Or_type, is_inductive=True))
    Or_inl_type = Pi("P", Sort(0),
                  Pi("Q", Sort(0),
                  Pi("p", Var("P"),
                     App(App(Const("Or"), Var("P")), Var("Q")))))
    env.add(Declaration("Or.inl", Or_inl_type))
    Or_inr_type = Pi("P", Sort(0),
                  Pi("Q", Sort(0),
                  Pi("q", Var("Q"),
                     App(App(Const("Or"), Var("P")), Var("Q")))))
    env.add(Declaration("Or.inr", Or_inr_type))

    # Iff (P Q : Prop) : Prop  :=  And (P → Q) (Q → P)
    Iff_type = Pi("P", Sort(0), Pi("Q", Sort(0), Sort(0)))
    Iff_def  = Lam("P", Sort(0),
                Lam("Q", Sort(0),
                    App(App(Const("And"),
                            Pi("_", Var("P"), Var("Q"))),
                            Pi("_", Var("Q"), Var("P")))))
    env.add(Declaration("Iff", Iff_type, Iff_def))
    Iff_intro_type = Pi("P", Sort(0),
                     Pi("Q", Sort(0),
                     Pi("mp", Pi("_", Var("P"), Var("Q")),
                     Pi("mpr", Pi("_", Var("Q"), Var("P")),
                        App(App(Const("Iff"), Var("P")), Var("Q"))))))
    env.add(Declaration("Iff.intro", Iff_intro_type))

    # ── Quot (quotient types) ─────────────────────────────────────────────────
    # Axiomatic primitives: Quot, Quot.mk, Quot.lift, Quot.ind, Quot.sound.
    # Quot.lift gets is_inductive=True so whnf treats it as opaque until
    # try_quot_reduction fires (the same pattern as Nat.rec).

    # Quot : (alpha : Type) -> (r : alpha -> alpha -> Prop) -> Type
    Quot_type = Pi("alpha", Sort(1),
                Pi("r", Pi("_", Var("alpha"), Pi("_", Var("alpha"), Sort(0))),
                   Sort(1)))
    env.add(Declaration("Quot", Quot_type, is_inductive=True))

    # Quot.mk : (alpha : Type) -> (r : alpha -> alpha -> Prop) -> alpha -> Quot alpha r
    Quot_mk_type = Pi("alpha", Sort(1),
                   Pi("r", Pi("_", Var("alpha"), Pi("_", Var("alpha"), Sort(0))),
                   Pi("a", Var("alpha"),
                      App(App(Const("Quot"), Var("alpha")), Var("r")))))
    env.add(Declaration("Quot.mk", Quot_mk_type))

    # Quot.lift : (alpha beta : Type) -> (r : alpha -> alpha -> Prop) ->
    #             (f : alpha -> beta) ->
    #             (h : forall a b, r a b -> Eq beta (f a) (f b)) ->
    #             Quot alpha r -> beta
    Quot_lift_type = Pi("alpha", Sort(1),
                     Pi("beta", Sort(1),
                     Pi("r", Pi("_", Var("alpha"), Pi("_", Var("alpha"), Sort(0))),
                     Pi("f", Pi("_", Var("alpha"), Var("beta")),
                     Pi("h", Pi("a", Var("alpha"),
                               Pi("b", Var("alpha"),
                               Pi("_", App(App(Var("r"), Var("a")), Var("b")),
                                  App(App(App(Const("Eq"), Var("beta")),
                                         App(Var("f"), Var("a"))),
                                         App(Var("f"), Var("b")))))),
                     Pi("q", App(App(Const("Quot"), Var("alpha")), Var("r")),
                        Var("beta")))))))
    env.add(Declaration("Quot.lift", Quot_lift_type, is_inductive=True))

    # Quot.ind : (alpha : Type) -> (r : alpha -> alpha -> Prop) ->
    #            (beta : Quot alpha r -> Prop) ->
    #            (forall a, beta (Quot.mk alpha r a)) ->
    #            forall q, beta q
    Quot_ind_type = Pi("alpha", Sort(1),
                    Pi("r", Pi("_", Var("alpha"), Pi("_", Var("alpha"), Sort(0))),
                    Pi("beta", Pi("_", App(App(Const("Quot"), Var("alpha")), Var("r")), Sort(0)),
                    Pi("step", Pi("a", Var("alpha"),
                                 App(Var("beta"),
                                     App(App(App(Const("Quot.mk"), Var("alpha")), Var("r")), Var("a")))),
                    Pi("q", App(App(Const("Quot"), Var("alpha")), Var("r")),
                       App(Var("beta"), Var("q")))))))
    env.add(Declaration("Quot.ind", Quot_ind_type, is_inductive=True))

    # Quot.sound : (alpha : Type) -> (r : alpha -> alpha -> Prop) ->
    #              (a b : alpha) -> r a b ->
    #              Eq (Quot alpha r) (Quot.mk alpha r a) (Quot.mk alpha r b)
    # Pure axiom -- no value, no reduction rule.
    Quot_sound_type = Pi("alpha", Sort(1),
                      Pi("r", Pi("_", Var("alpha"), Pi("_", Var("alpha"), Sort(0))),
                      Pi("a", Var("alpha"),
                      Pi("b", Var("alpha"),
                      Pi("_", App(App(Var("r"), Var("a")), Var("b")),
                         App(App(App(Const("Eq"), App(App(Const("Quot"), Var("alpha")), Var("r"))),
                                    App(App(App(Const("Quot.mk"), Var("alpha")), Var("r")), Var("a"))),
                                    App(App(App(Const("Quot.mk"), Var("alpha")), Var("r")), Var("b"))))))))
    env.add(Declaration("Quot.sound", Quot_sound_type))

    # ── Bool ─────────────────────────────────────────────────────────────────
    # inductive Bool : Type where
    #   | false : Bool
    #   | true  : Bool
    #
    # Bool.rec is the eliminator / if-then-else for Bool.
    # When motive is non-dependent (fun _ => T), it is literally:
    #   if b then tval else fval
    #
    # Bool.rec : (motive : Bool → Type) →
    #            motive Bool.false →
    #            motive Bool.true  →
    #            (b : Bool) → motive b
    env.add(Declaration("Bool", Sort(1), is_inductive=True))
    env.add(Declaration("Bool.false", Const("Bool")))
    env.add(Declaration("Bool.true",  Const("Bool")))

    # Bool.rec  : motive lives in Type  (Sort 1)  — for data-valued case splits
    # Bool.recP : motive lives in Prop  (Sort 0)  — for proof-valued case splits
    # In Lean both are auto-generated as the same recursor with universe polymorphism.
    # We provide both as separate constants; the iota rule fires for either name.
    Bool_rec_type = Pi(
        "motive", Pi("_", Const("Bool"), Sort(1)),
        Pi("fval", App(Var("motive"), Const("Bool.false")),
        Pi("tval", App(Var("motive"), Const("Bool.true")),
        Pi("b",    Const("Bool"),
                   App(Var("motive"), Var("b"))))))
    env.add(Declaration("Bool.rec", Bool_rec_type, is_inductive=True))

    Bool_recP_type = Pi(
        "motive", Pi("_", Const("Bool"), Sort(0)),   # motive : Bool → Prop
        Pi("fval", App(Var("motive"), Const("Bool.false")),
        Pi("tval", App(Var("motive"), Const("Bool.true")),
        Pi("b",    Const("Bool"),
                   App(Var("motive"), Var("b"))))))
    env.add(Declaration("Bool.casesOn", Bool_recP_type, is_inductive=True))

    # ── Bool operations (defined via Bool.rec) ────────────────────────────────
    # Bool.not : Bool → Bool
    #   Bool.not b = Bool.rec (fun _ => Bool) Bool.true Bool.false b
    Bool_not_type = Pi("b", Const("Bool"), Const("Bool"))
    Bool_not_def  = Lam("b", Const("Bool"),
                        App(App(App(App(
                            Const("Bool.rec"),
                            Lam("_", Const("Bool"), Const("Bool"))),  # motive
                            Const("Bool.true")),                        # false branch → true
                            Const("Bool.false")),                       # true  branch → false
                            Var("b")))
    env.add(Declaration("Bool.not", Bool_not_type, Bool_not_def))

    # Bool.and : Bool → Bool → Bool
    #   Bool.and a b = Bool.rec (fun _ => Bool) Bool.false b a
    #   (if a then b else false)
    Bool_and_type = Pi("a", Const("Bool"), Pi("b", Const("Bool"), Const("Bool")))
    Bool_and_def  = Lam("a", Const("Bool"),
                    Lam("b", Const("Bool"),
                        App(App(App(App(
                            Const("Bool.rec"),
                            Lam("_", Const("Bool"), Const("Bool"))),  # motive
                            Const("Bool.false")),                        # false branch → false
                            Var("b")),                                    # true  branch → b
                            Var("a"))))
    env.add(Declaration("Bool.and", Bool_and_type, Bool_and_def))

    # Bool.or : Bool → Bool → Bool
    #   Bool.or a b = Bool.rec (fun _ => Bool) b Bool.true a
    #   (if a then true else b)
    Bool_or_type = Pi("a", Const("Bool"), Pi("b", Const("Bool"), Const("Bool")))
    Bool_or_def  = Lam("a", Const("Bool"),
                   Lam("b", Const("Bool"),
                       App(App(App(App(
                           Const("Bool.rec"),
                           Lam("_", Const("Bool"), Const("Bool"))),   # motive
                           Var("b")),                                    # false branch → b
                           Const("Bool.true")),                          # true  branch → true
                           Var("a"))))
    env.add(Declaration("Bool.or", Bool_or_type, Bool_or_def))

    # Bool.xor : Bool → Bool → Bool
    #   Bool.xor a b = Bool.rec (fun _ => Bool) b (Bool.not b) a
    #   (if a then Bool.not b else b)
    Bool_xor_type = Pi("a", Const("Bool"), Pi("b", Const("Bool"), Const("Bool")))
    Bool_xor_def  = Lam("a", Const("Bool"),
                    Lam("b", Const("Bool"),
                        App(App(App(App(
                            Const("Bool.rec"),
                            Lam("_", Const("Bool"), Const("Bool"))),   # motive
                            Var("b")),                                    # false branch → b
                            App(Const("Bool.not"), Var("b"))),            # true  branch → not b
                            Var("a"))))
    env.add(Declaration("Bool.xor", Bool_xor_type, Bool_xor_def))

    # Bool.beq : Bool → Bool → Bool   (boolean equality)
    #   Bool.beq a b = Bool.rec (fun _ => Bool) (Bool.not b) b a
    #   (if a then b else Bool.not b)
    Bool_beq_type = Pi("a", Const("Bool"), Pi("b", Const("Bool"), Const("Bool")))
    Bool_beq_def  = Lam("a", Const("Bool"),
                    Lam("b", Const("Bool"),
                        App(App(App(App(
                            Const("Bool.rec"),
                            Lam("_", Const("Bool"), Const("Bool"))),   # motive
                            App(Const("Bool.not"), Var("b"))),           # false branch → not b
                            Var("b")),                                    # true  branch → b
                            Var("a"))))
    env.add(Declaration("Bool.beq", Bool_beq_type, Bool_beq_def))

    # Nat.beq : Nat → Nat → Bool   (decidable equality on Nat)
    #   Nat.beq 0     0     = true
    #   Nat.beq 0     (s m) = false
    #   Nat.beq (s n) 0     = false
    #   Nat.beq (s n) (s m) = Nat.beq n m
    #
    # We implement by Nat.rec on n with motive (fun _ => Nat → Bool).
    # The induction hypothesis ih : Nat → Bool is the recursive call.
    # The step returns a Nat → Bool function by doing Nat.rec on m.
    #
    # Nat.rec
    #   (fun _ => Nat → Bool)          -- motive
    #   (fun m => Nat.rec ... true (fun _ _ => false) m)  -- 0 case: 0 =? m
    #   (fun n' ih m => Nat.rec ... false (fun m' _ => ih m') m)  -- succ case
    #   n
    # then apply to m
    Nat_beq_type = Pi("n", Const("Nat"), Pi("m", Const("Nat"), Const("Bool")))
    # zero_case: fun m => if m=0 then true else false
    zero_case = Lam("m2", Const("Nat"),
                  App(App(App(App(
                    Const("Nat.rec"),
                    Lam("_", Const("Nat"), Const("Bool"))),  # motive
                    Const("Bool.true")),                       # 0 = 0 → true
                    Lam("_m1", Const("Nat"),
                    Lam("_ih", Const("Bool"),
                        Const("Bool.false")))),                # 0 = succ → false
                    Var("m2")))
    # succ_case: fun n' ih => fun m => if m=0 then false else ih (pred m)
    succ_case = Lam("_n1", Const("Nat"),
                Lam("ih", Pi("_", Const("Nat"), Const("Bool")),
                  Lam("m2", Const("Nat"),
                    App(App(App(App(
                      Const("Nat.rec"),
                      Lam("_", Const("Nat"), Const("Bool"))),  # motive
                      Const("Bool.false")),                      # succ = 0 → false
                      Lam("m3", Const("Nat"),
                      Lam("_ih2", Const("Bool"),
                          App(Var("ih"), Var("m3"))))),           # succ = succ → ih m3
                      Var("m2")))))
    Nat_beq_def = Lam("n", Const("Nat"),
                  Lam("m", Const("Nat"),
                    App(
                      App(App(App(App(
                        Const("Nat.rec"),
                        Lam("_", Const("Nat"), Pi("_", Const("Nat"), Const("Bool")))),
                        zero_case),
                        succ_case),
                        Var("n")),
                      Var("m"))))
    env.add(Declaration("Nat.beq", Nat_beq_type, Nat_beq_def))

    # Nat.ble : Nat → Nat → Bool   (n ≤ m ?)
    #   Nat.ble 0     _     = true
    #   Nat.ble (s n) 0     = false
    #   Nat.ble (s n) (s m) = Nat.ble n m
    Nat_ble_type = Pi("n", Const("Nat"), Pi("m", Const("Nat"), Const("Bool")))
    ble_zero_case = Lam("_m", Const("Nat"), Const("Bool.true"))
    ble_succ_case = Lam("_n1", Const("Nat"),
                    Lam("ih", Pi("_", Const("Nat"), Const("Bool")),
                      Lam("m2", Const("Nat"),
                        App(App(App(App(
                          Const("Nat.rec"),
                          Lam("_", Const("Nat"), Const("Bool"))),
                          Const("Bool.false")),                      # succ n ≤ 0 → false
                          Lam("m3", Const("Nat"),
                          Lam("_ih2", Const("Bool"),
                              App(Var("ih"), Var("m3"))))),           # succ n ≤ succ m3 → n ≤ m3
                          Var("m2")))))
    Nat_ble_def = Lam("n", Const("Nat"),
                  Lam("m", Const("Nat"),
                    App(
                      App(App(App(App(
                        Const("Nat.rec"),
                        Lam("_", Const("Nat"), Pi("_", Const("Nat"), Const("Bool")))),
                        ble_zero_case),
                        ble_succ_case),
                        Var("n")),
                      Var("m"))))
    env.add(Declaration("Nat.ble", Nat_ble_type, Nat_ble_def))

    # ── Bool ↔ Prop bridge ────────────────────────────────────────────────────
    # Bool.decide : Bool → Prop
    #   Bool.decide Bool.true  = True
    #   Bool.decide Bool.false = False
    # This is the bridge from Bool computation to Prop reasoning.
    # In Lean this is called `decide` / `Decidable`; we keep it simple.
    Bool_decide_type = Pi("b", Const("Bool"), Sort(0))
    Bool_decide_def  = Lam("b", Const("Bool"),
                           App(App(App(App(
                               Const("Bool.rec"),
                               Lam("_", Const("Bool"), Sort(0))),  # motive: Bool → Prop
                               Const("False")),                      # false → False
                               Const("True")),                       # true  → True
                               Var("b")))
    env.add(Declaration("Bool.decide", Bool_decide_type, Bool_decide_def))

    # Bool.ite : (T : Type) → Bool → T → T → T
    #   Bool.ite T b t e = Bool.rec (fun _ => T) e t b
    # This is the non-dependent if/then/else.  The parser desugars
    #   if b then t else e  into  Bool.ite T b t e
    # where T must be supplied by the user (or inferred from context).
    # We expose this as a first-class function so users can also call it
    # directly without the sugar.
    Bool_ite_type = Pi("T", Sort(1),
                    Pi("b", Const("Bool"),
                    Pi("t", Var("T"),
                    Pi("e", Var("T"),
                       Var("T")))))
    Bool_ite_def  = Lam("T", Sort(1),
                    Lam("b", Const("Bool"),
                    Lam("t", Var("T"),
                    Lam("e", Var("T"),
                        App(App(App(App(
                            Const("Bool.rec"),
                            Lam("_", Const("Bool"), Var("T"))),  # motive: fun _ => T
                            Var("e")),                             # false branch
                            Var("t")),                             # true  branch
                            Var("b"))))))
    env.add(Declaration("Bool.ite", Bool_ite_type, Bool_ite_def))

        # ── Nat.add ───────────────────────────────────────────────────────────────
    # def Nat.add : Nat → Nat → Nat
    #   | n, 0      => n
    #   | n, succ m => succ (Nat.add n m)
    # Defined via Nat.rec on the second argument.
    add_type = Pi("n", Const("Nat"), Pi("m", Const("Nat"), Const("Nat")))
    # add n m = Nat.rec (motive := fun _ => Nat) n (fun m' ih => Nat.succ ih) m
    add_def = Lam("n", Const("Nat"),
              Lam("m", Const("Nat"),
                App(App(App(App(
                  Const("Nat.rec"),
                  Lam("_", Const("Nat"), Const("Nat"))),   # motive: Nat → Nat (trivial)
                  Var("n")),                                 # base case: n + 0 = n
                  Lam("m1", Const("Nat"),                   # step: n + (succ m1) = succ (n + m1)
                  Lam("ih", Const("Nat"),
                      App(Const("Nat.succ"), Var("ih"))))),
                  Var("m"))))                               # major premise: recurse on m
    env.add(Declaration("Nat.add", add_type, add_def))

    # ── Nat.mul ───────────────────────────────────────────────────────────────
    # def Nat.mul : Nat → Nat → Nat
    #   | _, 0      => 0
    #   | n, succ m => Nat.add (Nat.mul n m) n
    mul_type = Pi("n", Const("Nat"), Pi("m", Const("Nat"), Const("Nat")))
    mul_def = Lam("n", Const("Nat"),
             Lam("m", Const("Nat"),
               App(App(App(App(
                 Const("Nat.rec"),
                 Lam("_", Const("Nat"), Const("Nat"))),  # motive: Nat → Nat
                 Const("Nat.zero")),                       # base: n * 0 = 0
                 Lam("m1", Const("Nat"),
                 Lam("ih", Const("Nat"),
                   App(App(Const("Nat.add"), Var("ih")), Var("n"))))),
                 Var("m"))))                               # major premise: recurse on m
    env.add(Declaration("Nat.mul", mul_type, mul_def))

    return env


# ──────────────────────────────────────────────────────────────────────────────
# 7.  SURFACE PARSER
#     A hand-written recursive-descent parser for a Lean-flavoured syntax.
# ──────────────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    pass


class Parser:
    """
    Tokens and grammar (simplified Lean 4 syntax):

        term  ::= lam | pi | arrow | app
        lam   ::= 'fun' binders '=>' term
        pi    ::= '∀' binders ',' term
        arrow ::= app ('→' term)?
        app   ::= atom atom*
        atom  ::= '(' term ')' | Nat_lit | ident | 'Prop' | 'Type' | 'Sort'
        binders ::= ('(' ident ':' term ')')+
    """

    def __init__(self, text: str):
        self.tokens = tokenize(text)
        self.pos = 0

    def peek(self) -> str:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ""

    def consume(self, expected: Optional[str] = None) -> str:
        tok = self.peek()
        if expected and tok != expected:
            raise ParseError(f"expected '{expected}', got '{tok}'")
        self.pos += 1
        return tok

    def at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    # ── Grammar rules ─────────────────────────────────────────────────────────

    def parse_term(self) -> Term:
        return self.parse_arrow()

    def parse_arrow(self) -> Term:
        """Parse  A → B  (right-associative, non-dependent)."""
        left = self.parse_app()
        if self.peek() == "→":
            _ = self.consume("→")
            right = self.parse_term()
            return Pi("_", left, right)
        return left

    def parse_forall(self) -> Term:
        """∀ (x : A), B"""
        _ = self.consume("∀")
        binders = self.parse_binders()
        _ = self.consume(",")
        body = self.parse_term()
        for v, vt in reversed(binders):
            body = Pi(v, vt, body)
        return body

    def parse_lam(self) -> Term:
        """fun (x : A) => body"""
        _ = self.consume("fun")
        binders = self.parse_binders()
        _ = self.consume("=>")
        body = self.parse_term()
        for v, vt in reversed(binders):
            body = Lam(v, vt, body)
        return body

    def parse_binders(self) -> list[tuple[str, Term]]:
        """Parse one or more (x : T) binder groups."""
        binders = []
        while self.peek() == "(":
            _ = self.consume("(")
            names = []
            while self.peek() not in (":", ""):
                names.append(self.consume())
            _ = self.consume(":")
            typ = self.parse_term()
            _ = self.consume(")")
            for n in names:
                binders.append((n, typ))
        if not binders:
            raise ParseError("expected binder '(x : T)'")
        return binders

    def parse_app(self) -> Term:
        """Left-associative function application."""
        if self.peek() == "fun":
            return self.parse_lam()
        if self.peek() == "∀":
            return self.parse_forall()
        if self.peek() == "if":
            return self.parse_if()

        func = self.parse_atom()
        while self.peek() and self.peek() not in (
            ")", ",", "=>", "→", ":=", ":", "#", "where", "theorem",
            "def", "axiom", "example", "check", "eval", "print",
            "then", "else",
        ):
            arg = self.parse_atom()
            func = App(func, arg)
        return func

    def parse_if(self) -> Term:
        """if b then t else e  =>  Bool.rec (fun (_ : Bool) => _) e t b
        The motive is inferred by the type checker; we use a fresh variable
        as a placeholder that will unify during type inference of Bool.rec.
        In practice the user writes Bool.rec directly when a dependent motive
        is needed; 'if' is sugar for the non-dependent case.
        """
        _ = self.consume("if")
        cond = self.parse_app()
        _ = self.consume("then")
        t_branch = self.parse_app()
        _ = self.consume("else")
        e_branch = self.parse_term()
        # Desugar: if b then t else e  =>  Bool.ite T b t e
        # Bool.ite is defined in the env as:
        #   fun (T:Type) (b:Bool) (t e : T) => Bool.rec (fun _ => T) e t b
        # The caller must supply T as the first explicit argument; here we
        # emit just the three visible parts and let the user supply T, OR
        # we use the convention that `if` at the term level is 3-arg:
        #   Bool.ite <type> <cond> <then> <else>
        # For convenience we also support writing:
        #   if b then t else e   (T inferred from branch type by Bool.rec)
        # by emitting Bool.rec with a fresh motive variable — the kernel
        # resolves the motive via definitional equality on the branches.
        # We use Var("_T") as a placeholder; it gets resolved by context.
        # Desugar to Bool.ite applied to Bool (the result type).
        # This makes `if b then t else e` work for Bool-valued expressions.
        # For other result types, use Bool.ite T b t e directly.
        return App(App(App(App(Const("Bool.ite"), Const("Bool")), cond), t_branch), e_branch)

    def parse_atom(self) -> Term:
        tok = self.peek()
        if not tok:
            raise ParseError("unexpected end of input")

        if tok == "(":
            _ = self.consume("(")
            t = self.parse_term()
            _ = self.consume(")")
            return t

        if tok == "Prop":
            _ = self.consume()
            return Sort(0)

        if tok == "Type":
            _ = self.consume()
            # Type alone = Sort 1; Type n = Sort (n+1)
            nxt = self.peek()
            if nxt and re.match(r"^\d+$", nxt):
                n = int(self.consume())
                return Sort(n + 1)
            return Sort(1)

        if tok == "Sort":
            _ = self.consume()
            n = int(self.consume())
            return Sort(n)

        if tok == "fun":
            return self.parse_lam()

        if tok == "∀":
            return self.parse_forall()

        if re.match(r"^\d+$", tok):
            _ = self.consume()
            return NatLit(int(tok))

        # Bool literals — sugar for Bool.true / Bool.false
        if tok == "true":
            _ = self.consume()
            return Const("Bool.true")
        if tok == "false":
            _ = self.consume()
            return Const("Bool.false")

        if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", tok):
            _ = self.consume()
            # Always parse as Var. The kernel resolves names: if a name is
            # bound in the local context, it's a variable; if it's in the
            # global environment, it becomes a Const at infer time.
            # Using Var uniformly avoids the heuristic of uppercase=global.
            return Var(tok)

        raise ParseError(f"unexpected token '{tok}'")


def tokenize(text: str) -> list[str]:
    """Split source text into tokens."""
    # Normalise Unicode arrows
    text = text.replace("->", "→")
    # Normalise "all"
    text = text.replace("@", "∀")
    # Insert spaces around special characters
    for ch in ("(", ")", ",", ":", "="):
        text = text.replace(ch, f" {ch} ")
    # But keep := together
    text = re.sub(r": =", ":=", text)
    # And => together
    text = re.sub(r"= >", "=>", text)
    tokens = text.split()
    return tokens


# ──────────────────────────────────────────────────────────────────────────────
# 8.  COMMAND PROCESSOR
#     Lean-style top-level commands.
# ──────────────────────────────────────────────────────────────────────────────

class Kernel:
    """
    The top-level state: environment + command executor.
    Commands mirror Lean 4:
        theorem <name> : <type> := <proof>
        def     <name> : <type> := <body>
        axiom   <name> : <type>
        #check  <term>
        #eval   <term>
        #print  <name>
        example : <type> := <proof>
    """

    def __init__(self):
        self.env = build_initial_env()
        self.verbose = True

    def run_command(self, text: str):
        text = text.strip()
        if not text or text.startswith("--"):
            return

        # Strip inline comments
        if " --" in text:
            text = text[:text.index(" --")]

        try:
            self._dispatch(text)
        except (KernelError, ParseError) as e:
            print(f"  ✗  {e}")

    def _dispatch(self, text: str):
        if text.startswith("#check"):
            self._cmd_check(text[len("#check"):].strip())
        elif text.startswith("#eval"):
            self._cmd_eval(text[len("#eval"):].strip())
        elif text.startswith("#print"):
            self._cmd_print(text[len("#print"):].strip())
        elif text.startswith("theorem "):
            self._cmd_def(text, is_theorem=True)
        elif text.startswith("def "):
            self._cmd_def(text, is_theorem=False)
        elif text.startswith("axiom "):
            self._cmd_axiom(text)
        elif text.startswith("example "):
            self._cmd_example(text)
        elif text.startswith("-- "):
            pass   # comment
        else:
            # Try to parse as a bare term and check it
            self._cmd_check(text)

    # ── #check ────────────────────────────────────────────────────────────────
    def _cmd_check(self, src: str):
        term = self._parse(src)
        ty   = infer(self.env, {}, term)
        ty_n = normalize(self.env, {}, ty)
        # If the term is a bare name that is a definition, show name not body
        if isinstance(term, (Var, Const)) and self.env.has(term.name):
            print(f"  {term.name} : {ty_n}")
        else:
            t_n  = normalize(self.env, {}, term)
            print(f"  {t_n} : {ty_n}")

    # ── #eval ─────────────────────────────────────────────────────────────────
    def _cmd_eval(self, src: str):
        term = self._parse(src)
        _    = infer(self.env, {}, term)   # type-check first
        norm = normalize(self.env, {}, term)
        print(f"  {norm}")

    # ── #print ────────────────────────────────────────────────────────────────
    def _cmd_print(self, name: str):
        name = name.strip()
        decl = self.env.lookup(name)
        kind = "axiom" if decl.value is None else "def/theorem"
        print(f"  {kind} {decl.name} : {normalize(self.env, {}, decl.type)}")
        if decl.value is not None:
            print(f"    := {normalize(self.env, {}, decl.value)}")

    # ── theorem / def ─────────────────────────────────────────────────────────
    def _cmd_def(self, text: str, is_theorem: bool):
        # Syntax: (theorem|def) <name> : <type> := <body>
        kw = "theorem" if is_theorem else "def"
        rest = text[len(kw):].strip()
        if ":=" not in rest:
            raise ParseError(f"missing ':=' in {kw} declaration")
        head, body_src = rest.split(":=", 1)
        if ":" not in head:
            raise ParseError(f"missing ':' in {kw} declaration")
        name, type_src = head.split(":", 1)
        name = name.strip()

        ty   = self._parse(type_src.strip())
        body = self._parse(body_src.strip())

        # Verify the type is well-formed
        ty_sort = infer(self.env, {}, ty)
        _ = ensure_sort(self.env, {}, ty_sort)

        # Verify the body has the declared type
        check(self.env, {}, body, ty)

        self.env.add(Declaration(name, ty, body))
        kind = "theorem" if is_theorem else "def"
        print(f"  ✓  {kind} '{name}' accepted")

    # ── axiom ─────────────────────────────────────────────────────────────────
    def _cmd_axiom(self, text: str):
        rest = text[len("axiom"):].strip()
        if ":" not in rest:
            raise ParseError("missing ':' in axiom declaration")
        name, type_src = rest.split(":", 1)
        name = name.strip()
        ty   = self._parse(type_src.strip())
        ty_sort = infer(self.env, {}, ty)
        _ = ensure_sort(self.env, {}, ty_sort)
        self.env.add(Declaration(name, ty))
        print(f"  ✓  axiom '{name}' accepted")

    # ── example ───────────────────────────────────────────────────────────────
    def _cmd_example(self, text: str):
        rest = text[len("example"):].strip()
        if ":=" not in rest:
            raise ParseError("missing ':=' in example")
        type_src, body_src = rest.split(":=", 1)
        if type_src.startswith(":"):
            type_src = type_src[1:]
        ty   = self._parse(type_src.strip())
        body = self._parse(body_src.strip())
        ty_sort = infer(self.env, {}, ty)
        _ = ensure_sort(self.env, {}, ty_sort)
        check(self.env, {}, body, ty)
        print(f"  ✓  example accepted (proof term: {normalize(self.env, {}, body)})")

    # ── helper ────────────────────────────────────────────────────────────────
    def _parse(self, src: str) -> Term:
        p = Parser(src)
        t = p.parse_term()
        if not p.at_end():
            raise ParseError(f"unexpected token(s) after term: {p.tokens[p.pos:]}")
        return t


# ──────────────────────────────────────────────────────────────────────────────
# 9.  REPL
# ──────────────────────────────────────────────────────────────────────────────

BANNER = """\
╔══════════════════════════════════════════════════════════════════╗
║        Lean-like Dependent Type Theory REPL (Python)             ║
║                                                                  ║
║  Universe hierarchy (mirrors Lean 4):                            ║
║    Sort 0  =  Prop   (impredicative universe of propositions)    ║
║    Sort 1  =  Type   (= Type 0, universe of ordinary types)      ║
║    Sort n  =  Type (n-1)   for n ≥ 1                             ║
║    Sort n  :  Sort (n+1)   (Prop : Type, Type : Type 1, …)       ║
║                                                                  ║
║  Commands:                                                       ║
║    theorem <n> : <type> := <proof>                               ║
║    def     <n> : <type> := <body>                                ║
║    axiom   <n> : <type>                                          ║
║    example    : <type> := <proof>                                ║
║    #check  <term>   -- show type                                 ║
║    #eval   <term>   -- normalise                                 ║
║    #print  <name>   -- show declaration                          ║
║    :quit  or  Ctrl-D  to exit                                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

def run_repl():
    kernel = Kernel()
    print(BANNER)
    while True:
        try:
            line = input("⊢ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if line in (":quit", ":q", "quit"):
            print("Goodbye.")
            break
        if not line:
            continue
        kernel.run_command(line)


def run_script(path: str):
    """Execute a .lean-like script file non-interactively.

    Multi-line commands are joined: a command continues until we see
    a ':=' (end-of-declaration marker) or a blank line separates it,
    or a new top-level keyword begins.
    Blank lines and pure-comment lines are printed as-is.
    """
    kernel = Kernel()
    print(f"── Running script: {path} ──\n")
    with open(path) as f:
        raw_lines = f.readlines()

    TOP_LEVEL = ("theorem ", "def ", "axiom ", "example ", "#check", "#eval", "#print")

    def is_top(line: str) -> bool:
        s = line.strip()
        return any(s.startswith(kw) for kw in TOP_LEVEL)

    # Collect logical lines by joining physical lines until the command ends.
    # A command ends when the accumulated text contains ':=' (for definitions)
    # or is a directive (#check etc.) or the next physical line starts a new
    # top-level keyword.
    logical_lines: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            logical_lines.append(" ".join(current))
            current.clear()

    for raw in raw_lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush()
            logical_lines.append("")   # blank line marker
            continue

        if stripped.startswith("--"):
            flush()
            logical_lines.append(line)
            continue

        # If we're accumulating and this line starts a new top-level, flush first
        if current and is_top(stripped):
            flush()

        current.append(stripped)

        # A command is complete when:
        #   - It's a directive (#check / #eval / #print)
        #   - It's a theorem/def with ':=' AND a non-empty body after ':='
        #   - It's a bare expression (not starting with a keyword)
        joined = " ".join(current)
        j = joined.lstrip()
        is_directive = any(j.startswith(kw) for kw in ("#check", "#eval", "#print"))
        is_decl = any(j.startswith(kw) for kw in ("theorem ", "def ", "axiom ", "example "))
        if is_directive:
            flush()
        elif is_decl:
            if ":=" in j:
                after = j.split(":=", 1)[1].strip()
                if after:   # body is non-empty
                    flush()
            # axiom has no ':=', complete after one logical line
            elif j.startswith("axiom ") and ":" in j:
                flush()
        elif not is_top(j):
            # bare expression — flush immediately
            flush()

    flush()

    # Now execute logical lines
    for line in logical_lines:
        if not line:
            print()
            continue
        if line.strip().startswith("--"):
            print(line)
            continue
        print(f"⊢ {line}")
        kernel.run_command(line)


# ──────────────────────────────────────────────────────────────────────────────
# 10. ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_script(sys.argv[1])
    else:
        run_repl()
