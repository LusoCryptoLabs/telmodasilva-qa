"""Turns a JUnit report into a short Markdown summary for the CI job page."""

import sys
import xml.etree.ElementTree as ET
from collections import Counter


def main(path: str) -> None:
    cases = ET.parse(path).getroot().iter("testcase")
    counts: Counter[str] = Counter()
    failures: list[str] = []
    for case in cases:
        name = f"{case.get('classname')}::{case.get('name')}"
        skipped = case.find("skipped")
        if case.find("failure") is not None or case.find("error") is not None:
            counts["failed"] += 1
            failures.append(name)
        elif skipped is not None:
            kind = "xfailed" if skipped.get("type") == "pytest.xfail" else "skipped"
            counts[kind] += 1
        else:
            counts["passed"] += 1

    print("### telmodasilva.pt\n")
    print("| passed | failed | known issues (xfail) | skipped |")
    print("|---|---|---|---|")
    row = [counts[key] for key in ("passed", "failed", "xfailed", "skipped")]
    print("| " + " | ".join(str(n) for n in row) + " |")
    if failures:
        print("\nFailed:\n")
        for name in failures:
            print(f"- `{name}`")


if __name__ == "__main__":
    main(sys.argv[1])
