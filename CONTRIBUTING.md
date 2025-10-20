# Contributing to Prompt2Figma

First off, thank you for considering contributing to Prompt2Figma! It's people like you that make Prompt2Figma such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@prompt2figma.com](mailto:conduct@prompt2figma.com).

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.8+
- **Redis** server
- **Git** 2.0+
- **Figma Desktop App** (for plugin development)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/prompt2Figma.git
cd prompt2Figma
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/ORGANIZATION/prompt2Figma.git
```

4. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

### Installation

#### Backend Setup
```bash
cd prompt2Figma-Backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
npm install  # For AST validation
```

#### Frontend Setup
```bash
cd "prompt2Figma-Frontend (Plugin)"
npm install
npm run build
```

---

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Urgent fixes for production
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

**Examples:**
```bash
feature/add-dark-mode
bugfix/fix-device-selector
docs/update-api-documentation
refactor/improve-state-management
```

### Keep Your Fork Updated

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### Making Changes

1. **Create a branch** from `main`
2. **Make your changes** following our coding standards
3. **Test your changes** thoroughly
4. **Commit your changes** following commit guidelines
5. **Push to your fork**
6. **Open a Pull Request**

---

## Coding Standards

### TypeScript/JavaScript

- Use **TypeScript** for type safety
- Follow **ESLint** configuration
- Use **2 spaces** for indentation
- Maximum line length: **100 characters**
- Use **camelCase** for variables and functions
- Use **PascalCase** for classes and types
- Add **JSDoc comments** for public APIs

**Example:**
```typescript
/**
 * Validates user input for security issues.
 * @param input - The user input to validate
 * @returns Sanitized input string
 * @throws {ValidationError} If input contains malicious content
 */
function validateInput(input: string): string {
  // Implementation
}
```

### Python

- Follow **PEP 8** style guide
- Use **4 spaces** for indentation
- Maximum line length: **100 characters**
- Use **snake_case** for functions and variables
- Use **PascalCase** for classes
- Add **docstrings** for all functions and classes

**Example:**
```python
def validate_session_id(session_id: str) -> bool:
    """
    Validate that a session ID has the correct format.
    
    Args:
        session_id: The session ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Implementation
```

### CSS

- Use **BEM methodology** for class names
- Use **2 spaces** for indentation
- Group related properties together
- Use **CSS variables** for colors and spacing
- Add comments for complex selectors

**Example:**
```css
/* Component: Device Selector */
.device-selector {
  padding: 20px;
  border-radius: 8px;
}

.device-selector__button {
  padding: 12px 18px;
  transition: all 0.2s ease;
}

.device-selector__button--active {
  background: var(--color-primary);
}
```

---

## Commit Guidelines

We follow the **Conventional Commits** specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `build` - Build system changes

### Examples

```bash
feat(plugin): add dark mode support

Add dark mode toggle to plugin UI with theme persistence.
Includes automatic theme detection based on Figma settings.

Closes #123

---

fix(backend): resolve session timeout issue

Fix race condition in session cleanup that caused premature
session expiration. Add additional logging for debugging.

Fixes #456

---

docs(readme): update installation instructions

Add troubleshooting section and clarify Redis setup steps.
Include Windows-specific instructions.

---

refactor(ui): improve device selector component

Extract device selector logic into separate module.
Add comprehensive unit tests and improve accessibility.
```

### Commit Message Rules

1. Use **imperative mood** ("add" not "added")
2. Don't capitalize first letter
3. No period at the end of subject
4. Limit subject line to **50 characters**
5. Wrap body at **72 characters**
6. Separate subject from body with blank line
7. Use body to explain **what** and **why**, not how

---

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug code
- [ ] Branch is up to date with main
- [ ] Commit messages follow guidelines

### PR Title Format

Use the same format as commit messages:

```
feat(plugin): add export to PNG feature
fix(backend): resolve memory leak in state store
docs(api): update endpoint documentation
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings

## Related Issues
Closes #123
Relates to #456
```

### Review Process

1. **Automated Checks** - CI/CD must pass
2. **Code Review** - At least 1 approval required
3. **Testing** - Reviewer tests changes locally
4. **Documentation** - Verify docs are updated
5. **Merge** - Squash and merge to main

### After Merge

- Delete your branch
- Update your local repository
- Close related issues

---

## Testing

### Running Tests

#### Backend Tests
```bash
cd prompt2Figma-Backend
pytest tests/ -v
pytest --cov=app tests/  # With coverage
```

#### Frontend Tests
```bash
cd "prompt2Figma-Frontend (Plugin)"
npm test
npm run test:coverage
```

### Writing Tests

- Write tests for all new features
- Maintain >80% code coverage
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

**Example:**
```typescript
describe('DeviceSelector', () => {
  it('should toggle device selection on click', () => {
    // Arrange
    const selector = new DeviceSelector();
    
    // Act
    selector.selectDevice('mobile');
    
    // Assert
    expect(selector.getSelectedDevice()).toBe('mobile');
  });
});
```

---

## Documentation

### Code Documentation

- Add JSDoc/docstrings for all public APIs
- Include parameter types and return types
- Provide usage examples
- Document edge cases and limitations

### README Updates

Update README.md when:
- Adding new features
- Changing installation steps
- Modifying configuration
- Adding dependencies

### API Documentation

- Document all endpoints
- Include request/response examples
- Specify error codes
- Add authentication requirements

---

## Questions?

- **General Questions**: Open a [Discussion](https://github.com/ORGANIZATION/prompt2Figma/discussions)
- **Bug Reports**: Open an [Issue](https://github.com/ORGANIZATION/prompt2Figma/issues)
- **Feature Requests**: Open an [Issue](https://github.com/ORGANIZATION/prompt2Figma/issues) with `enhancement` label
- **Security Issues**: Email [security@prompt2figma.com](mailto:security@prompt2figma.com)

---

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project website (if applicable)

Thank you for contributing to Prompt2Figma! 🎉
