---
description: Review changes for clean, modular, non-excessive code
argument-hint: "[scope]"
---
Review the current changes/scope for clean code and maintainability: $ARGUMENTS

Focus on:
- unnecessary abstraction or over-engineering
- excessive file/class/method size
- unclear names
- duplicated logic
- too many conditionals
- hidden side effects
- weak error handling
- test gaps
- upgrade/API/integration compatibility risk

Return:
1. Keep
2. Change
3. Delete/simplify
4. Risk
5. Suggested smaller design

Do not edit files unless I explicitly ask.
