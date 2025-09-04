# Clean up nicestlog migrate output - Remove confusing and irrelevant steps

Task goal
- Fix the confusing "recommended steps" and "next steps and guidance" in migrate output
- Remove irrelevant suggestions like "add nicestlog dependencies" (already installed)
- Remove "initialize nicestlog configuration" (already done)
- Remove out-of-scope suggestions like "create translation files", "review CLI styling"
- Simplify to only show relevant next steps: run migrate (interactive or dry-run)
- Make the migrate output actually "nice" instead of overwhelming

Out-of-scope for this task
- Writing any new code functionality
- Changing core migration logic
- Adding new features

General approach (guardrails)
- English artifacts (Rule 7)
- No dependency YOLOing (Rule 3). Use `uv run` for Python commands
- Lint before committing (Rule 5). Respect pre-commit if present (Rule 6)
- Only add tests when we change code (Rule 4)

Prioritized work items (with checkboxes)

1) Investigate current migrate output and identify problems
   - Context: User reports confusing output with irrelevant steps
   - Files to check/modify:
     - Run `uv run nicestlog migrate` to see current output
     - Find where "recommended steps" and "next steps" are generated
     - Identify all the problematic suggestions mentioned
   - Steps:
     - [x] Run migrate command and capture current output
     - [x] Find source code generating "recommended steps"
     - [x] Find source code generating "next steps and guidance"
     - [x] Identify where dependency/config detection happens
     - [x] Document all problematic suggestions to remove
     - **FOUND PROBLEMS**:
       - Line 594-631 in project_analyzer.py: "Add nicestlog to dependencies" (wrong when already installed)
       - Line 596+ in project_analyzer.py: "Initialize nicestlog configuration" (wrong when already done)
       - Lines 597-600: Out-of-scope suggestions like "Create translation files", "Review CLI styling"
       - Line 2550 in cli.py: "Recommended Steps" section
       - Line 2334 in cli.py: "Next Steps & Guidance" section with greenfield setup for existing projects
       - Lines 2375-2379: Wrong suggestions like "nicestlog docs --feature logging" and "demo basic"

2) Remove irrelevant and confusing suggestions
   - Context: Steps like "add dependencies" and "init config" are wrong when already done
   - Files to check/modify:
     - Migration analysis/recommendation logic
     - Output formatting functions
   - Steps:
     - [x] Remove "add nicestlog dependencies" when already installed
     - [x] Remove "initialize nicestlog configuration" when already done
     - [x] Remove out-of-scope suggestions (translations, CLI styling, etc.)
     - [x] Fix detection logic to recognize existing setup

3) Simplify and improve next steps guidance
   - Context: Should only show actually relevant next actions
   - Files to check/modify:
     - Next steps generation logic
     - Output formatting
   - Steps:
     - [x] Consolidate "recommended steps" and "next steps" into one clear section
     - [x] Focus on actual migration actions: run migrate, interactive mode
     - [x] Remove demo/docs suggestions (out of scope for migration)
     - [x] Make output concise and actionable

4) Test and verify improved output
   - Context: Ensure the cleaned up output is actually helpful
   - Files to check/modify:
     - Test migrate command output
   - Steps:
     - [x] Test migrate output on this project (should detect existing setup)
     - [x] Verify only relevant suggestions are shown
     - [x] Ensure output is clear and not overwhelming
     - [x] Commit with message: "fix(migrate): clean up confusing output and irrelevant suggestions"