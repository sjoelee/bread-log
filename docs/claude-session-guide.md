# Claude Session Guide

This document provides guidance for Claude Code sessions working on the bread-log project.

## 📋 Pre-Implementation Checklist

Before implementing any new features or making significant changes, Claude should:

### 1. Read All Documentation Files
**MANDATORY**: Read through ALL markdown files in the `/docs/` directory to understand:
- Project architecture and design decisions
- Database schema and relationships
- Known issues and solutions
- Implementation patterns and conventions

Key documentation files:
- `recipe-system.md` - Recipe versioning and relationships
- `database-notes.md` - Database implementation notes and gotchas
- `claude-session-guide.md` - This file
- Any other `.md` files in `/docs/` directory

### 2. Check for Research Documentation
Before implementing new features, look for:
- **Research documents** - Understanding of requirements, user needs, technical approach
- **TDD (Test-Driven Development) documents** - Test specifications and acceptance criteria
- Ask user if research/TDD docs exist for the feature being implemented

### 3. Understand Codebase Conventions
**CRITICAL**: Read through the existing codebase to understand:
- Code style and patterns
- Database query formats (use `%s` placeholders, NOT `$1`, `$2`)
- API endpoint patterns
- Error handling approaches
- File organization and naming conventions

## 🚫 Exceptions to Pre-Implementation Research

The user may provide explicit exceptions for:
- **Bug fixes** - Immediate fixes don't require full research
- **Small refactoring** - Code cleanup and optimization
- **Emergency issues** - Production problems requiring quick resolution
- **Explicitly stated exceptions** - User says "skip research for this task"

## 🔧 Implementation Guidelines

### Database Queries
- **Always use `%s` placeholders** in psycopg queries
- **Never use `$1`, `$2` style** placeholders (causes parameter mismatch errors)
- Reference `docs/database-notes.md` for specific database gotchas

### API Development
- Follow existing patterns in `service.py`
- Use proper HTTP status codes
- Include comprehensive error handling
- Add logging for debugging

### Frontend Development
- Follow existing React/TypeScript patterns
- Use existing UI components and styling
- Maintain consistency with current UX patterns

## 📁 Key Project Structure

```
/backend/
  - service.py (FastAPI endpoints)
  - db.py (Database layer)
  - models.py (Pydantic models)
  - recipe_service.py (Business logic)

/src/
  - BreadAppNew.tsx (Main app component)
  - components/ (React components)
  - hooks/ (Custom hooks)

/docs/
  - *.md (All documentation files)

/database/
  - *.sql (Database schema and migrations)
```

## 🎯 Session Workflow

1. **Start**: Read this guide and all `/docs/` files
2. **Research**: Check for feature research/TDD documents
3. **Explore**: Understand relevant codebase sections
4. **Plan**: Create implementation plan with user approval
5. **Implement**: Follow established patterns and conventions
6. **Test**: Verify functionality works as expected
7. **Document**: Update relevant documentation

## 💡 Quality Standards

- **Code Consistency**: Match existing patterns and style
- **Error Handling**: Comprehensive error handling and logging
- **User Experience**: Maintain intuitive and consistent UX
- **Performance**: Consider database efficiency and frontend performance
- **Documentation**: Update docs when making architectural changes

## 📞 When in Doubt

- Ask the user for clarification on requirements
- Reference existing similar implementations
- Follow the principle of least surprise
- Maintain backward compatibility unless explicitly changing

Remember: Taking time upfront to understand the codebase saves time and prevents bugs later!