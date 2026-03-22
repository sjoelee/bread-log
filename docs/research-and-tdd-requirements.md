# Research and TDD Requirements

## 🔬 Pre-Implementation Research Policy

Before implementing any new feature or significant change, Claude must check for and request the following documentation:

### Required Research Documentation

1. **Feature Research Document**
   - User requirements and acceptance criteria
   - Technical approach and architecture decisions
   - Integration points with existing system
   - Potential challenges and solutions

2. **Test-Driven Development (TDD) Document**
   - Test specifications and test cases
   - Expected behavior and edge cases
   - Performance requirements
   - Acceptance criteria for completion

### Research Document Locations

Check these locations for existing research:
- `/docs/research/` directory (if it exists)
- `/docs/` directory for feature-specific research files
- Project management tools or external documentation (ask user)

### When Research is Required

**ALWAYS required for:**
- New feature implementation
- Significant architectural changes
- Database schema modifications
- API endpoint additions or major changes
- UI/UX changes or new user flows

**Research may be skipped for:**
- Bug fixes (unless explicitly stated)
- Code refactoring and cleanup
- Performance optimizations
- Documentation updates
- User explicitly states "skip research"

## 📋 Research Request Template

When research documentation is missing, use this template:

```
I notice this task involves [new feature/significant change]. Before implementation, I'd like to check:

1. **Feature Research**: Do you have documentation covering:
   - User requirements and acceptance criteria
   - Technical approach and architecture decisions
   - Integration points with existing system

2. **TDD Documentation**: Do you have test specifications including:
   - Expected behavior and test cases
   - Performance requirements
   - Acceptance criteria

If these documents don't exist, would you like me to:
- Proceed with implementation based on the current request (with your explicit approval)
- Help create research documentation first
- Ask clarifying questions to understand requirements better

Please let me know your preference!
```

## 🚀 Implementation Without Full Research

If the user approves proceeding without complete research documentation:

1. **Document assumptions** made during implementation
2. **Ask clarifying questions** about ambiguous requirements
3. **Implement incrementally** with user feedback
4. **Create documentation** during implementation process
5. **Be prepared to refactor** based on user feedback

## 📝 Research Documentation Standards

When creating research documents:

### Feature Research Template
```markdown
# [Feature Name] Research

## User Requirements
- Primary user goals
- Acceptance criteria
- User stories

## Technical Approach
- Architecture decisions
- Database changes required
- API modifications needed
- Frontend changes required

## Integration Points
- How this connects to existing features
- Potential conflicts or dependencies

## Implementation Plan
- Step-by-step development approach
- Testing strategy
- Rollout considerations
```

### TDD Documentation Template
```markdown
# [Feature Name] Test Specifications

## Test Cases
- Unit tests required
- Integration tests required
- End-to-end test scenarios

## Expected Behavior
- Normal operation flows
- Edge cases and error conditions
- Performance expectations

## Acceptance Criteria
- Definition of "done"
- Success metrics
- Rollback criteria if needed
```

## 🎯 Benefits of Research-First Approach

1. **Reduces implementation time** by having clear direction
2. **Prevents scope creep** with defined requirements
3. **Improves code quality** with upfront design decisions
4. **Enables better testing** with predefined test cases
5. **Facilitates user approval** with shared understanding

## ⚡ Quick Implementation Exception Process

For urgent tasks where research is skipped:

1. User provides explicit "skip research" instruction
2. Claude documents what assumptions are being made
3. Implementation proceeds with frequent user check-ins
4. Research documentation created post-implementation for future reference

Remember: Research upfront saves debugging time later!