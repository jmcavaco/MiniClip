# AI Usage

## 1. What I Used AI For

I used AI to help me understand the requirements, improve and produce parts of the code and review edge cases. I treated AI suggestions as a starting point and made the final decisions myself. AI was also used to generate new loc.plist files to test the Tool.py.

## 2. What I Kept

- **[Findings]:** After manually checking both new and old .plist, the AI confirmed and added more information.
- **[Test Files]:** AI helped me produce loc.plist files to test functions through the development. This improved the time required to test the Tool.
- **[Generated Code]:** AI generated and kept parts of the code.
- **[Templates]:** Templates for the .md files.
 
## 3. What I Rejected or Changed

- **[`en-US` as always correct]:** AI suggested `en-US` language to be the ground truth, but I changed it because in a real world problem it could a mistake could happen to any language key. Implementing a majority of languages check.
- **[Detect every warning]:** AI initially faced the problem with too much complexity. Since the tool was specifically to help decide with a short time window that would not help. So I created a list of importance levels.
- **[Generated Code]:** Some parts of the code that was generated had to be changed or removed, in order to have better organization and functions to be split more efficiently and reusable even if the rest of the tool is to be discontinued.


## 4. How I Verified the Results

I reviewed the generated code and the output, checked that I understood the logic and tested relevant cases, including new .plist files. I also checked that the output matched the task requirements and the assumptions made.

## 5. What I Learned

AI helped me save time when generating test files, exploring possible implementations and identifying potential issues. However, I learned that AI-generated code can introduce unnecessary complexity or make assumptions that do not fit the real-world problem. Reviewing the suggestions, testing them against different localization files and adapting the implementation to the actual requirements were essential. The experience reinforced that AI is most useful as a development assistant, while the responsibility for the design, correctness and final result remains mine.

**Responsibility:** I take responsibility for the final implementation and can explain the decisions and trade-offs during a technical interview.