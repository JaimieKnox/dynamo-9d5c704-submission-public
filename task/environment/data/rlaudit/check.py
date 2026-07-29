"""Reconcile written audit documents against the expected documents a bundle ships."""

import argparse
import json
import os

TOL = 1e-6
FLOAT_FIELDS = ("mean_vtrace_target", "mean_pg_advantage", "mean_is_weight", "priority_sum_after")


def _diff_steps(got, expected):
    problems = []
    if len(got) != len(expected):
        problems.append("step count %d, expected %d" % (len(got), len(expected)))
        return problems
    for lhs, rhs in zip(got, expected):
        where = "step %s" % rhs.get("step")
        for field in ("step", "target_epoch", "dropped_nonresident", "sampled"):
            if lhs.get(field) != rhs.get(field):
                problems.append("%s: %s is %r, expected %r" % (where, field, lhs.get(field), rhs.get(field)))
        for field in FLOAT_FIELDS:
            left = lhs.get(field)
            right = rhs.get(field)
            if left is None or abs(left - right) > TOL:
                problems.append("%s: %s is %r, expected %r" % (where, field, left, right))
    return problems


def compare(got, expected):
    problems = []
    if got.get("bundle") != expected.get("bundle"):
        problems.append("bundle is %r, expected %r" % (got.get("bundle"), expected.get("bundle")))
    problems.extend(_diff_steps(got.get("steps", []), expected.get("steps", [])))
    got_totals = got.get("totals", {})
    exp_totals = expected.get("totals", {})
    for field in sorted(exp_totals):
        left = got_totals.get(field)
        right = exp_totals[field]
        if isinstance(right, float):
            if left is None or abs(left - right) > TOL:
                problems.append("totals.%s is %r, expected %r" % (field, left, right))
        elif left != right:
            problems.append("totals.%s is %r, expected %r" % (field, left, right))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reconcile audit documents against expectations.")
    parser.add_argument("--runs", default="/app/runs")
    parser.add_argument("--out", default="/app/out")
    args = parser.parse_args(argv)

    failures = 0
    checked = 0
    for name in sorted(os.listdir(args.runs)):
        expected_path = os.path.join(args.runs, name, "expected.json")
        if not os.path.isfile(expected_path):
            continue
        checked += 1
        got_path = os.path.join(args.out, name + ".json")
        if not os.path.isfile(got_path):
            print("%s MISSING %s" % (name, got_path))
            failures += 1
            continue
        with open(expected_path) as handle:
            expected = json.load(handle)
        with open(got_path) as handle:
            got = json.load(handle)
        problems = compare(got, expected)
        if problems:
            failures += 1
            print("%s MISMATCH" % name)
            for line in problems[:20]:
                print("  " + line)
        else:
            print("%s OK" % name)
    print("reconciled %d bundle(s), %d mismatching" % (checked, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
