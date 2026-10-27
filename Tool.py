
"""Compare two localisation plists.

Usage:
    python Tool.py OLD.plist NEW.plist

L1: Placeholder mismatch
L2: Empty / missing language / removed key
L3: Unusual number

Exit code 1 if any L1 or L2 finding.
L3 findings are shown only when there are no L1 or L2 findings.

Commands: ID = details | n = next | p = previous
          /text = search | f L1/L2/L3/all = filter | q = quit
"""
import plistlib
import re
import sys
from collections import Counter

TOKEN = re.compile(r"%(?:\d+\$)?[@diufs]|\{[^{}]*\}|[A-Z]:\[|\]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


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


def main(old_path, new_path):
    old, new = load(old_path), load(new_path)
    L1, L2, L3, fixed = [], [], [], []

    # L1: placeholder problems.
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

    # L2: removed keys remain individual findings.
    # Missing and empty translations are aggregated by language.
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

    # L3: numbers unique to one language.
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
                L3.append((
                    f"{key}: {lang} - unique numbers {sorted(odd)}",
                    f"KEY: {key}\n"
                    f"LANGUAGE: {lang}\n"
                    f"UNIQUE NUMBERS: {sorted(odd)}\n"
                    f"TEXT: {langs[lang]!r}"
                ))

    show_L3 = not (L1 or L2)
    verdict = (
        "NO-SHIP" if (L1 or L2)
        else "REVIEW" if L3
        else "OK"
    )

    # Verdict first.
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

    groups = [
        ("L1", "CRITICAL - Placeholder mismatches", L1),
        ("L2", "MISSING - Empty, missing, or removed text", L2),
        ("L3", "REVIEW - Possible gameplay issues",
         L3 if show_L3 else []),
    ]

    # Assign stable IDs across all visible findings.
    findings = []

    for code, title, items in groups:
        if not items:
            continue

        print(f"\n{code} | {title} ({len(items)} finding(s))")

        for summary, detail in items:
            finding_id = str(len(findings) + 1)
            findings.append({
                "id": finding_id,
                "code": code,
                "summary": summary,
                "detail": detail,
            })

    if L3 and not show_L3:
        print(
            f"\nL3 details deferred ({len(L3)} finding(s)); "
            "resolve L1/L2 findings first."
        )

    # Fixed issues are informational, not current risks.
    if fixed:
        print(f"\nFIXED - {len(fixed)} resolved issue(s)")
        print("-" * 64)

        for item in fixed:
            print(f"  + {item}")

    # Interactive paginated browser.
    if findings and sys.stdin.isatty():
        page_size = 15
        page = 0
        active_filter = "all"
        search_term = ""
        by_id = {item["id"]: item for item in findings}

        def matching_findings():
            result = findings

            if active_filter != "all":
                result = [
                    item for item in result
                    if item["code"].lower() == active_filter
                ]

            if search_term:
                needle = search_term.casefold()
                result = [
                    item for item in result
                    if needle in item["summary"].casefold()
                    or needle in item["detail"].casefold()
                ]

            return result

        def show_page():
            result = matching_findings()
            pages = max(
                1, (len(result) + page_size - 1) // page_size
            )
            current = min(page, pages - 1)

            print("\n" + "-" * 64)
            print(
                f"FINDINGS | {len(result)} matches | "
                f"page {current + 1}/{pages}"
            )
            print("-" * 64)

            start = current * page_size

            for item in result[start:start + page_size]:
                print(
                    f"  [{item['id']:>4}] "
                    f"{item['code']}  {item['summary']}"
                )

            print("\nCommands: ID = details | n = next | p = previous")
            print("          /text = search | f L1/L2/L3/all = filter | q = quit")

        show_page()

        while True:
            try:
                command = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if command.lower() in ("q", "quit", "exit", ""):
                break

            lower = command.lower()

            if lower == "n":
                page = min(
                    page + 1,
                    max(0, (len(matching_findings()) - 1) // page_size),
                )
                show_page()

            elif lower == "p":
                page = max(0, page - 1)
                show_page()

            elif command.startswith("/"):
                search_term = command[1:].strip()
                page = 0
                show_page()

            elif lower.startswith("f "):
                requested = lower[2:].strip()

                if requested not in ("all", "l1", "l2", "l3"):
                    print("Use: f all, f L1, f L2, or f L3")
                    continue

                active_filter = requested
                page = 0
                show_page()

            elif command in by_id:
                item = by_id[command]

                print("\n" + "-" * 64)
                print(f"FINDING ID: {item['id']}")
                print(f"TYPE: {item['code']}")
                print(item["detail"])
                print("-" * 64)

            else:
                print(
                    "Unknown command. Use an ID, n, p, /text, "
                    "f L1/L2/L3/all, or q."
                )

    print(
        f"\nFINAL VERDICT: {verdict} "
        f"(L1={len(L1)} L2={len(L2)} L3={len(L3)})"
    )

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
