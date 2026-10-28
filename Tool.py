
"""Compare two localisation plists.

Usage:
    python Tool.py OLD.plist NEW.plist

L1: Placeholder mismatch
L2: Empty / missing language / removed key
L3: Unusual number

Exit code 1 if any L1 or L2 finding.
L3 findings are shown only when there are no L1 or L2 findings.

Commands: ID = details | n = next | p = previous | f L1/L2/L3/all = filter | q = quit
"""
import plistlib
import re
import sys
from collections import Counter

TOKEN = re.compile(r"%(?:\d+\$)?[@diufs]|\{[^{}]*\}|[A-Z]:\[|\]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
PAGE_SIZE = 15

def tokens(text):
    found = TOKEN.findall(text)
    stray = TOKEN.sub("", text).count("%")
    return Counter(found + ["stray %"] * stray)


def numbers(text):
    text = TOKEN.sub("", text)
    return {f"{float(n.replace(',', '.')):g}" for n in NUMBER.findall(text)}


def load(path):
    with open(path, "rb") as stream:
        return plistlib.load(stream)["localisations"]


def placeholder_problems(data):
    bad, ties = {}, []

    for key, langs in data.items():
        texts = {
            lang: text for lang, text in langs.items()
            if isinstance(text, str) and text.strip()
        }

        if len(texts) < 2:
            continue

        sigs = {lang: tokens(text) for lang, text in texts.items()}
        top = Counter(
            tuple(sorted(sig.items())) for sig in sigs.values()
        ).most_common(2)

        if len(top) > 1 and top[0][1] == top[1][1]:
            ties.append(key)
            continue

        expected = top[0][0]

        for lang, signature in sigs.items():
            if tuple(sorted(signature.items())) != expected:
                bad[(key, lang)] = (dict(expected), dict(signature))

    return bad, ties

def check_l1(old, new):
    """L1: placeholder mismatches. Returns (findings, fixed)."""
    L1, fixed = [], []

    (old_bad, _), (new_bad, ties) = (
        placeholder_problems(old),
        placeholder_problems(new),
    )

    for (key, lang), (expected, found) in new_bad.items():
        text = new[key][lang]

        L1.append((
            f"{key}: {lang} - placeholder mismatch",
            f"KEY: {key}\n"
            f"LANGUAGE: {lang}\n"
            f"FOUND: {found or 'none'}\n"
            f"EXPECTED: {expected or 'none'}\n"
            f"TEXT: {text!r}"
        ))

    for key in ties:
        L1.append((
            f"{key}: language placeholders disagree",
            f"KEY: {key}\n"
            "DETAIL: Languages disagree and there is no majority.\n"
            "ACTION: Check placeholders manually."
        ))

    # Previously broken placeholders that are now fixed.
    for key, lang in old_bad:
        new_text = new.get(key, {}).get(lang, "")
        if (key, lang) not in new_bad and new_text.strip():
            fixed.append(
                f"{key} [{lang}] "
                f"{old[key][lang]!r} -> {new_text!r}"
            )

    return L1, fixed


def check_l2(old, new):
    """L2: removed keys, missing languages, empty translations."""
    L2 = []

    all_langs = {
        lang
        for data in (old, new)
        for langs in data.values()
        for lang in langs
    }

    missing_by_lang = {}
    empty_by_lang = {}

    for key in old:
        if key not in new:
            previous = next(iter(old[key].values()), None)

            L2.append((
                f"{key}: key removed",
                f"KEY: {key}\n"
                f"STATUS: REMOVED\n"
                f"OLD VALUE: {previous!r}"
            ))

    for key, langs in new.items():
        for lang in sorted(all_langs - set(langs)):
            missing_by_lang.setdefault(lang, []).append(key)

        for lang, text in langs.items():
            if not isinstance(text, str) or not text.strip():
                empty_by_lang.setdefault(lang, []).append(key)

    for lang, keys in sorted(missing_by_lang.items()):
        keys.sort()

        L2.append((
            f"{lang}: missing translation in {len(keys)} keys",
            f"LANGUAGE: {lang}\n"
            "ISSUE: MISSING TRANSLATION\n"
            f"COUNT: {len(keys)}\n"
            "AFFECTED KEYS:\n"
            + "\n".join(f"  - {key}" for key in keys)
        ))

    for lang, keys in sorted(empty_by_lang.items()):
        keys.sort()

        L2.append((
            f"{lang}: empty translation in {len(keys)} keys",
            f"LANGUAGE: {lang}\n"
            "ISSUE: EMPTY TRANSLATION\n"
            f"COUNT: {len(keys)}\n"
            "AFFECTED KEYS:\n"
            + "\n".join(f"  - {key}" for key in keys)
        ))

    return L2


def check_l3(new):
    """L3: numbers that appear in only one language."""
    L3 = []

    for key, langs in new.items():
        nums = {
            lang: numbers(text)
            for lang, text in langs.items()
            if isinstance(text, str) and text.strip()
        }

        for lang, found_numbers in nums.items():
            other_numbers = set().union(
                *(
                    values for other_lang, values in nums.items()
                    if other_lang != lang
                ),
                set(),
            )

            odd = found_numbers - other_numbers

            if odd and len(nums) >= 3:
                different_numbers = sorted(odd)
                expected_numbers = sorted(other_numbers)

                L3.append((
                    f"{key}: {lang} - different numbers {different_numbers}, "
                    f"expected numbers {expected_numbers}",
                    f"KEY: {key}\n"
                    f"LANGUAGE: {lang}\n"
                    f"DIFFERENT NUMBER(S): {different_numbers}\n"
                    f"EXPECTED NUMBER(S): {expected_numbers}\n"
                    f"TEXT: {langs[lang]!r}"
                ))

    return L3

def get_verdict(L1, L2, L3):
    if L1 or L2:
        return "NO-SHIP"
    if L3:
        return "REVIEW"
    return "OK"


def show_verdict(verdict, old_path, new_path, L1, L2, L3):
    print("\n" + "=" * 64)
    print("             LOCALISATION RELEASE CHECK")
    print("=" * 64)
    print(f"  VERDICT: {verdict}")
    print(f"  Baseline : {old_path}")
    print(f"  Candidate: {new_path}")
    print("-" * 64)
    print(f"  L1 - Placeholder mismatches : {len(L1)}")
    print(f"  L2 - Missing/empty text     : {len(L2)}")
    print(f"  L3 - Possible gameplay issue: {len(L3)}")

    if verdict == "NO-SHIP":
        print("  Action: Resolve all L1/L2 findings before shipping.")
    elif verdict == "REVIEW":
        print("  Action: Review L3 findings before shipping.")
    else:
        print("  Action: No issues detected by these checks.")

    print("=" * 64)


def build_groups(L1, L2, L3, show_L3):
    return [
        ("L1", "CRITICAL - Placeholder mismatches", L1),
        ("L2", "MISSING - Empty, missing, or removed text", L2),
        ("L3", "REVIEW - Possible gameplay issues", L3 if show_L3 else []),
    ]


def collect_findings(groups):
    """Give every visible finding a stable ID."""
    findings = []

    for code, title, items in groups:
        for summary, detail in items:
            findings.append({
                "id": str(len(findings) + 1),
                "code": code,
                "summary": summary,
                "detail": detail,
            })

    return findings


def show_groups(groups):
    for code, title, items in groups:
        if items:
            print(f"\n{code} | {title} ({len(items)} finding(s))")


def show_deferred(L3, show_L3):
    if L3 and not show_L3:
        print(
            f"\nL3 details deferred ({len(L3)} finding(s)); "
            "resolve L1/L2 findings first."
        )


def show_fixed(fixed):
    if not fixed:
        return

    print(f"\nFIXED - {len(fixed)} resolved issue(s)")
    print("-" * 64)

    for item in fixed:
        print(f"  + {item}")


def matching_findings(findings, active_filter, search_term):
    result = findings

    if active_filter != "all":
        result = [i for i in result if i["code"].lower() == active_filter]

    if search_term:
        needle = search_term.casefold()
        result = [
            i for i in result
            if needle in i["summary"].casefold()
            or needle in i["detail"].casefold()
        ]

    return result


def show_page(findings, page, active_filter, search_term):
    result = matching_findings(findings, active_filter, search_term)
    pages = max(1, (len(result) + PAGE_SIZE - 1) // PAGE_SIZE)
    current = min(page, pages - 1)

    print("\n" + "-" * 64)
    print(f"FINDINGS | {len(result)} matches | page {current + 1}/{pages}")
    print("-" * 64)

    start = current * PAGE_SIZE

    for item in result[start:start + PAGE_SIZE]:
        print(f"  [{item['id']:>4}] {item['code']}  {item['summary']}")

    print("\nCommands: ID = details | n = next | p = previous")
    print("      | f L1/L2/L3/all = filter | q = quit")


def show_detail(item):
    print("\n" + "-" * 64)
    print(f"FINDING ID: {item['id']}")
    print(f"TYPE: {item['code']}")
    print(item["detail"])
    print("-" * 64)


def browse(findings):
    """Interactive browser: pages, filter, search, details."""
    page = 0
    active_filter = "all"
    search_term = ""
    by_id = {item["id"]: item for item in findings}

    show_page(findings, page, active_filter, search_term)

    while True:
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        lower = command.lower()

        if lower in ("q", "quit", "exit", ""):
            break

        if lower == "n":
            last = max(0, (len(matching_findings(findings, active_filter, search_term)) - 1) // PAGE_SIZE)
            page = min(page + 1, last)
            show_page(findings, page, active_filter, search_term)

        elif lower == "p":
            page = max(0, page - 1)
            show_page(findings, page, active_filter, search_term)

        elif lower.startswith("f "):
            requested = lower[2:].strip()

            if requested not in ("all", "l1", "l2", "l3"):
                print("Use: f all, f L1, f L2, or f L3")
                continue

            active_filter = requested
            page = 0
            show_page(findings, page, active_filter, search_term)

        elif command in by_id:
            show_detail(by_id[command])

        else:
            print("Unknown command. Use an ID, n, p, f L1/L2/L3/all, or q.")


def show_final(verdict, L1, L2, L3):
    print(f"\nFINAL VERDICT: {verdict} (L1={len(L1)} L2={len(L2)} L3={len(L3)})")

def main(old_path, new_path):
    old, new = load(old_path), load(new_path)

    L1, fixed = check_l1(old, new)
    L2 = check_l2(old, new)
    L3 = check_l3(new)

    show_L3 = not (L1 or L2)
    verdict = get_verdict(L1, L2, L3)
    groups = build_groups(L1, L2, L3, show_L3)
    findings = collect_findings(groups)

    show_verdict(verdict, old_path, new_path, L1, L2, L3)
    show_groups(groups)
    show_deferred(L3, show_L3)
    show_fixed(fixed)

    if findings and sys.stdin.isatty():
        browse(findings)

    show_final(verdict, L1, L2, L3)

    return 1 if (L1 or L2) else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    try:
        sys.exit(main(sys.argv[1], sys.argv[2]))
    except (OSError, KeyError, plistlib.InvalidFileException) as exc:
        print(f"ERROR: Could not read localisation plist: {exc}",
              file=sys.stderr)
        sys.exit(2)
