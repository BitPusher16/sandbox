#!/usr/bin/env bash
# validate.sh — run all lean_repl example scripts and report pass/fail counts

REPL="$(dirname "$0")/lean_repl.py"
SCRIPTS=(
    ex1_logic.leanrepl
    ex2_nat.leanrepl
    ex3_induction.leanrepl
    ex4_quotients.leanrepl
    ex5_bool.leanrepl
)

total_pass=0
total_fail=0
any_failed=0

for script in "${SCRIPTS[@]}"; do
    path="$(dirname "$0")/$script"
    if [[ ! -f "$path" ]]; then
        echo "MISSING  $script"
        any_failed=1
        continue
    fi

    output=$(python "$REPL" "$path" 2>&1)
    pass=$(echo "$output" | grep -c "✓")
    fail=$(echo "$output" | grep -c "✗")

    if [[ $fail -eq 0 ]]; then
        printf "OK       %-30s  %d ✓\n" "$script" "$pass"
    else
        printf "FAIL     %-30s  %d ✓  %d ✗\n" "$script" "$pass" "$fail"
        echo "$output" | grep "✗" | sed 's/^/         /'
        any_failed=1
    fi

    total_pass=$((total_pass + pass))
    total_fail=$((total_fail + fail))
done

echo "─────────────────────────────────────────────────────"
printf "         %-30s  %d ✓  %d ✗\n" "total" "$total_pass" "$total_fail"

exit $any_failed
