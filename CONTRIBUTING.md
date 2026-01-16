# Contributing to TinySA Coordinator

Thank you for your interest in contributing to TinySA Coordinator! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful and considerate in all interactions
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Accept constructive criticism gracefully

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/frequency-scanner.git
   cd frequency-scanner
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/cj-vana/frequency-scanner.git
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- (Optional) TinySA Ultra hardware for testing device features

### Installation

Using Make (recommended):

```bash
make install          # Install all dependencies
make dev              # Start both backend and frontend servers
```

Or manually:

```bash
# Backend setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..
```

### Running Development Servers

```bash
# Using Make
make dev-backend      # Start backend on http://localhost:8000
make dev-frontend     # Start frontend on http://localhost:5173

# Or use the script
./scripts/run_dev.sh
```

### API Documentation

When the backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Making Changes

### Workflow

1. **Sync with upstream** before starting work:
   ```bash
   git fetch upstream
   git checkout develop
   git merge upstream/develop
   ```

2. **Create a feature branch** from `develop`:
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

3. **Make your changes** in small, logical commits

4. **Test your changes** thoroughly

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** against the `develop` branch

### Branch Naming Conventions

- `feature/` - New features (e.g., `feature/export-pdf`)
- `fix/` - Bug fixes (e.g., `fix/websocket-disconnect`)
- `docs/` - Documentation changes (e.g., `docs/api-examples`)
- `refactor/` - Code refactoring (e.g., `refactor/scan-service`)
- `test/` - Test additions or fixes (e.g., `test/preset-api`)

## Coding Standards

### Backend (Python)

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for function parameters and return values
- Use async/await for I/O operations
- Place business logic in the `services/` layer
- Use Pydantic schemas for request/response validation

**Linting and Formatting:**

```bash
# Check code style
ruff check backend/

# Format code
ruff format backend/

# Type checking
mypy backend/ --ignore-missing-imports
```

### Frontend (TypeScript/React)

- Use TypeScript for all new code
- Follow React hooks patterns (functional components)
- Use React Query for server state management
- Use Tailwind CSS for styling
- Keep components focused and reusable

**Linting:**

```bash
cd frontend
npm run lint          # ESLint
npx tsc --noEmit      # TypeScript type checking
```

### General Guidelines

- Write self-documenting code with clear variable/function names
- Add comments only when the logic isn't self-evident
- Keep functions small and focused on a single responsibility
- Avoid over-engineering - implement only what's needed now
- Don't introduce breaking changes without discussion

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) for clear, structured commit messages.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, semicolons, etc.)
- `refactor` - Code refactoring (no feature or bug changes)
- `test` - Adding or updating tests
- `chore` - Maintenance tasks (dependencies, build, etc.)
- `perf` - Performance improvements
- `ci` - CI/CD changes

### Scopes

Common scopes include:
- `api` - Backend API changes
- `frontend` - Frontend application
- `websocket` - WebSocket functionality
- `export` - Export features (WWB, WSM, CSV)
- `presets` - Frequency presets
- `history` - Scan history
- `device` - TinySA device communication
- `db` - Database changes
- `docker` - Docker configuration

### Examples

```bash
feat(export): add PDF export format support
fix(websocket): handle reconnection on network interruption
docs(api): add examples for preset endpoints
refactor(frontend): extract chart component from ScanPage
test(api): add unit tests for export service
chore(deps): update React to v19
```

## Pull Request Process

1. **Ensure all checks pass**:
   - Linting (backend and frontend)
   - Type checking
   - Tests (if applicable)
   - Build completes successfully

2. **Fill out the PR template** completely:
   - Describe what the PR does
   - Link related issues
   - List any breaking changes
   - Include screenshots for UI changes

3. **Keep PRs focused**:
   - One feature or fix per PR
   - Small, reviewable changes are preferred
   - Split large changes into multiple PRs if possible

4. **Respond to feedback** promptly and make requested changes

5. **Squash commits** if requested before merging

### PR Checklist

Before submitting:

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated (if applicable)
- [ ] Documentation updated (if applicable)
- [ ] No unrelated changes included
- [ ] Commits follow conventional commit format
- [ ] Branch is up to date with `develop`

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS and version
   - Python version
   - Node.js version
   - Browser (for frontend issues)
   - TinySA firmware version (if relevant)
6. **Screenshots/Logs**: If applicable

### Feature Requests

When requesting features:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: Your idea for addressing it
3. **Alternatives**: Other approaches you've considered
4. **Additional Context**: Mockups, examples, or references

## Testing

### Backend Testing

```bash
# Run all backend tests
make test

# Or directly with pytest
source venv/bin/activate
pytest backend/ -v
```

### Frontend Testing

```bash
cd frontend
npm test              # Run tests (when available)
npm run lint          # Lint check
npx tsc --noEmit      # Type check
```

### Manual Testing

For hardware-related features:
1. Connect a TinySA Ultra device
2. Verify the device appears in the application
3. Test scan operations
4. Verify export formats work correctly

## Documentation

- Update README.md for user-facing changes
- Update CLAUDE.md for development workflow changes
- Add JSDoc/docstrings for complex functions
- Update API documentation for endpoint changes

## Questions?

If you have questions or need help:

1. Check existing [issues](https://github.com/cj-vana/frequency-scanner/issues) for similar questions
2. Open a new issue with the "question" label
3. Be specific about what you need help with

Thank you for contributing to TinySA Coordinator!
