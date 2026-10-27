# Findings: Localisation Review

The localisation checker helps identify potential issues in `localisations_1_2_1.plist`, including inconsistent placeholders, missing translations, empty values, and numbers that differ between languages.

## Highest-risk issues

The highest-risk issues are **placeholder inconsistencies and missing translations**. Incorrect placeholders may cause strings to display incorrectly or lead to runtime formatting problems. Missing or empty translations can result in incomplete user-facing text.

Removed keys should also be checked to make sure they are no longer needed by the application. Numeric differences are lower priority because they may be intentional.

The tool should be used to identify potential problems, not to replace manual review. Its results need to be checked before making changes.

## Recommendations

I recommend using the tool as a **pre-release check initially**. The team can run it before each release, review the findings, and fix important issues before shipping.

Once the tool is reliable, it could be added to CI or used as a pre-merge check to catch problems earlier. L1 and L2 issues should be reviewed before merging, while L3 findings can be checked manually.

This approach helps the team catch localisation problems earlier and reduces the risk of shipping broken or incomplete translations.