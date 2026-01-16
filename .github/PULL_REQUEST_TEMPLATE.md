## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the appropriate option with an "x" -->

- [ ] `feat`: New feature (non-breaking change that adds functionality)
- [ ] `fix`: Bug fix (non-breaking change that fixes an issue)
- [ ] `docs`: Documentation only changes
- [ ] `refactor`: Code refactoring (no functional changes)
- [ ] `test`: Adding or updating tests
- [ ] `chore`: Maintenance tasks (dependencies, CI, etc.)
- [ ] `breaking`: Breaking change (fix or feature causing existing functionality to change)

## Areas Affected

<!-- Mark areas this PR touches -->

- [ ] Backend (Python/FastAPI)
- [ ] Frontend (React/TypeScript)
- [ ] Database/Models
- [ ] API Routes
- [ ] WebSocket
- [ ] TinySA Hardware Communication
- [ ] Docker/Deployment
- [ ] CI/CD

## Checklist

<!-- Ensure your PR meets these requirements -->

### General
- [ ] My code follows the project's coding style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary (complex logic only)
- [ ] My changes generate no new warnings

### Backend Changes
- [ ] I have run `ruff check backend/` and fixed any issues
- [ ] I have run `ruff format backend/`
- [ ] I have run `mypy backend/ --ignore-missing-imports`
- [ ] I have added/updated Pydantic schemas as needed

### Frontend Changes
- [ ] I have run `npm run lint` and fixed any issues
- [ ] I have run `npx tsc -b --noEmit` for type checking
- [ ] Components follow existing patterns (hooks, React Query)

### Testing
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally

## Related Issues

<!-- Link any related issues using "Fixes #123" or "Relates to #123" -->

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

## Additional Notes

<!-- Any additional context or information reviewers should know -->
