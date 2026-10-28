# Findings: `localisations_1_2_1.plist` vs live `1.2.0`

**Recommendation: do not ship as is.** The tool returns NO-SHIP: 2 placeholder findings (L1), 3 missing-content findings (L2), 1 fix.

## Highest risk (fix before shipping)
1. **Spanish (`es`) is missing from all 4 keys.** It was in the live file, so this is a regression, and it looks like an export problem. Spanish players fall back to another language. *Biggest impact.*
2. **"Starting in %u...", Russian:** now `До начала %...` (was `%u`). The countdown number is lost or the client misreads the format string.
3. **"Starting in %u...", Italian:** now an empty string (was `Inizio tra %u...`).
4. **"I just reached number 1", Italian:** the `B:[` group is never closed and the `A:` group is missing, so the share text will not parse.
5. **"Play as Guest" (`7a794655`) was removed entirely.** Fine if intentional; confirm no client code still uses it.

## Hidden until the above are fixed
- **Portuguese (pt-BR), `9bb069bc`:** the number 3 appears only in this language (others say 30), most likely a 3-second vs 30-second penalty. The tool reports it as an L3 count, so a releaser could miss it. Read it before shipping.

## A change that looks scary but is a fix
French `Commence dans % ...` (malformed in production) became `%u...`. The tool lists it under FIXED.

## Not caught by the tool (found by reading, or known gaps)
- **Turkish "I just reached number 1"** has 2 options in `B:[...]` where the others have 3. The placeholder check only counts brackets, so it passes.
- The version string in the candidate is still `1.2.0`.
- New `jp` language: the code is probably meant to be `ja`.
- Meaning errors (for example Italian "massimo" where it means minimum) need a native reviewer.

## How I'd propose the team uses it
1. **CI or pre-merge check** on any change to a localisation file: exit code `1` blocks the merge, and the printed summary goes on the PR.
2. **Manual run by the releaser** before the final go/no-go, against the file that is live, so fixes and already-live problems don't block a release.
3. Treat L3 as "read before release", not as a failure. Add checks only when each has a low false-alarm rate, so the report keeps being read.