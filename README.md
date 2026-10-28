# Localisation release check

```
python Tool.py localisations_1_2_0.plist localisations_1_2_1.plist
```
Python 3+, standard library only. Read-only: it never edits a file. Exit code `0` = no L1/L2 findings, `1` = L1/L2 findings, `2` = a file could not be read. In a terminal it opens a small browser (`ID`, `n`, `p`, `f L1/L2/L3/all`, `q`); when piped (CI) it prints the summary only.

## What I focused on and why
Failures that reach players without anyone noticing, because a line-by-line diff can't show them: a placeholder lost or malformed (crash or literal `%u` on screen), text that is missing or empty, and a number that disagrees with the other languages. A releaser has minutes, so the report opens with one verdict and groups findings by severity.

## How I decided what to check
Each check answers "what does the client do if this is wrong?" and is cheap to run with few false alarms.
- **L1 Placeholders (critical).** For each text ID, every language's placeholders (`%u`, `%@`, `%1$d`, `{0}`, stray `%`, and choice-group markers like `A:[` and `]`) are counted as an unordered set. The **majority** is the expected set. Languages that differ are flagged.
- **L2 Missing content.** Removed keys, languages missing from keys, empty strings. Repeats are grouped by language, so one dropped language is one finding.
- **L3 Unusual numbers.** A number that appears in one language and in none of the others (30 vs 3). Shown only when there are no L1/L2 findings, to keep the report short. 
- **Fixes.** The live file is checked the same way, so a placeholder that was broken and is now correct is listed as FIXED rather than as a risk.

## What it does not catch (blind spots)
- **Choice-group option counts:** `B:[a/b/c]` vs `B:[a/b]` looks identical, because only the brackets are counted.
- **A dropped number:** L3 only sees extra numbers, not missing ones.
- **Meaning errors,** tone and terminology, and whether a deleted key is still used by the client.
- **Layout:** text length, line-break count, stray whitespace; **language codes** such as `jp`; the **version string**.
- **A wrong majority** (several languages broken the same way) and keys with fewer than 3 translations.
- **Wrong Translation** It would increase the number of warnings exponentially.
- **Test coverage** I created additional .plist files to test the implemented checks, but they do not cover every possible error or warning. The tool is intended to highlight likely issues, not guarantee that all localisation problems are detected.

## Scope and trade-offs
- **Smallest complete version:** placeholder majority vote plus a verdict. **Added after:** L2, L3, baseline comparison (fixes), the browser.
- **Detect only,** no auto-fix: it can't know where a placeholder belongs, and silent fixes would hide a broken export.
- **L3 is hidden behind L1/L2** to avoid burying critical findings. The trade-off is that a real L3 issue stays invisible until the others are fixed; the summary still shows its count.
- **Not done:** JSON output, a test suite, thresholds in a config file.

## Next, with another day
Count and compare choice-group options, check the version string and language codes, flag changed line breaks and length, add a few broken sample files with tests, run it in CI on every change to a localisation file. With larger files and more time the tool could be improved to capture future known game crashers.

## Assumptions
The baseline is the file currently live; L3 findings give false information to certain languages and can affect gameplay; `en-US` is just another language; the tool runs before release, by a person or in CI.