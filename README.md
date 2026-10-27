# Localisation Plist Checker

A Python command-line tool for comparing two localisation `.plist` files to identify translation inconsistencies, missing entries, empty translations, and suspicious numeric differences.

The tool compares an **old version** against a **new version**, highlights current risks, and tracks previously reported placeholder issues that have been resolved.

## Features

- **L1 — Placeholder inconsistencies:** Detects differences in format placeholders, such as `%@`, `%d`, or positional placeholders, across languages. Uses the majority pattern to identify likely inconsistencies; ties are flagged for manual review.
- **L2 — Localisation completeness:** Detects removed keys, missing language entries, and empty translations.
- **L3 — Numeric inconsistencies:** Flags numbers that appear in only one language for a key. These findings are shown only when there are no L1 or L2 issues.
- **Fixed issues:** Identifies placeholder issues found in the old file that no longer appear in the new file. Fixed issues are reported separately from current risks.
- **Aggregated findings:** Groups missing entries by language and empty translations by language to reduce repetitive output.
- **Interactive findings browser:** Browse findings by page, search by text, filter by severity, and inspect individual findings.

## Requirements

- Python 3
- Two valid property list (`.plist`) files

The tool uses Python standard-library modules and does not require third-party packages.

## Usage

Place the script and your plist files in the same directory, then run:

```bash
python Tool.py
```

By default, the script compares:

- `OLD.plist` — the previous localisation version
- `NEW.plist` — the updated localisation version

Ensure these filenames match the paths configured in the script.

## Checks Explained

### L1 — Placeholder inconsistencies

Format placeholders are compared across language translations for the same key.

For example:

```text
English: "Hello, %@"
French:  "Bonjour"
German:  "Hallo, %@"
```

The French translation is flagged because it does not contain the placeholder used by the majority of languages.

The tool reports the key, affected language, found placeholder pattern, expected pattern, and translation text where available.

**Important:** Majority-based comparison is a heuristic. If most languages share the same incorrect placeholder pattern, the tool may not detect the underlying mistake. Review ties and ambiguous cases manually.

### L2 — Localisation completeness

The tool checks for:

- **Removed keys:** Keys present in the old file but absent from the new file.
- **Missing language entries:** Keys that do not have an entry for a language.
- **Empty translations:** Entries that exist but contain an empty translation.

Missing entries and empty translations are aggregated by language to make large reports easier to review. Removed keys remain individual findings.

### L3 — Numeric inconsistencies

The tool checks for numbers that occur in only one language for a given key.

For example, if a translation mentions `30` while the corresponding translations in other languages mention only `20`, the tool may flag the discrepancy.

Numbers may legitimately differ between translations, so treat these findings as review suggestions rather than definitive errors.

L3 findings are shown only when there are no L1 or L2 findings.

## Interactive Findings Browser

When findings are available, the browser lets you inspect them without printing the entire report at once.

| Command | Action |
|---|---|
| `n` | Next page |
| `p` | Previous page |
| `/text` | Search findings for text |
| `f L1` | Show only L1 findings |
| `f L2` | Show only L2 findings |
| `f L3` | Show only L3 findings |
| `f all` | Show all findings |
| `q` | Quit the browser |

Findings are displayed in pages of 15 entries. Finding IDs remain stable so you can open a specific finding for more detail.

When inspecting a finding, the detail view uses fields such as:

```text
KEY:
LANGUAGE:
FOUND:
EXPECTED:
TEXT:
```

Not every field applies to every finding type.

## Output

The report starts with an overall verdict, followed by current findings and a separate section for resolved placeholder issues.

- **Current risks** represent issues detected in the new localisation file.
- **Fixed issues** represent placeholder problems detected in the old file that are no longer detected in the new file.

Resolved issues are informational and are not counted as current risks.

## Exit Codes

| Exit code | Meaning |
|---|---|
| `0` | No L1 or L2 issues were detected. |
| `1` | One or more L1 or L2 issues were detected. |

L3 findings alone do not cause the tool to exit with code `1`.

## Limitations

- Placeholder validation relies on patterns found across languages rather than an authoritative source-language definition.
- Majority voting can miss errors shared by most languages.
- Numeric differences may be intentional and require human review.
- The checks do not replace linguistic review or validation in the application itself.

## Suggested Workflow

1. Update `NEW.plist` with the localisation changes.
2. Run the checker against `OLD.plist` and `NEW.plist`.
3. Review L1 and L2 findings first.
4. Use the interactive browser to search and inspect specific findings.
5. Review L3 findings when no L1 or L2 issues remain.
6. Confirm that resolved issues are genuinely fixed.
7. Run the checker again after making corrections.

