# Contributing to PullData

Thank you for your interest in contributing to PullData! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/pulldata.git
cd pulldata
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Code Style

We use several tools to maintain code quality:

- **black**: Code formatting (line length: 100)
- **ruff**: Linting and import sorting
- **mypy**: Type checking

Run all checks:
```bash
# Format code
black pulldata/

# Lint
ruff check pulldata/

# Type check
mypy pulldata/

# Or run all at once
pre-commit run --all-files
```

### Testing

We use pytest for testing. All new features should include tests.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pulldata --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run tests matching a pattern
pytest -k "test_pdf"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures for common setup
- Aim for >80% code coverage

Example:
```python
import pytest
from pulldata.parsing import PDFParser

@pytest.fixture
def sample_pdf():
    return "tests/fixtures/sample.pdf"

def test_pdf_parsing(sample_pdf):
    parser = PDFParser()
    result = parser.parse(sample_pdf)
    assert result.text is not None
    assert len(result.pages) > 0
```

## Contributing Guidelines

### Branching Strategy

- `main`: Stable, production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Commit Messages

Follow the conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(parser): add DOCX table extraction support

fix(storage): resolve race condition in FAISS index updates

docs(readme): update installation instructions
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes with clear, atomic commits
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all tests pass and code is formatted
6. Push your branch and create a pull request
7. Respond to review feedback

PR Title Format:
```
[Type] Brief description of changes
```

PR Description Template:
```markdown
## Description
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
How to test these changes.

## Related Issues
Closes #123
```

### Code Review

All PRs require:
- At least one approval from a maintainer
- All CI checks passing
- No merge conflicts
- Up-to-date with target branch

## Areas for Contribution

### High Priority
- Additional output formats (CSV, HTML, etc.)
- Performance optimizations
- Documentation improvements
- Bug fixes
- Test coverage improvements

### Feature Ideas
- Streaming generation for large reports
- Multi-modal support (images, charts)
- Advanced table processing
- Custom embedding models
- Integration with cloud storage
- Web UI

### Documentation
- Tutorial notebooks
- Video guides
- API documentation
- Architecture deep-dives
- Performance tuning guides

## Performance Considerations

When contributing, keep in mind:
- Target hardware: Tesla P4 (8GB VRAM)
- Optimize for speed and memory efficiency
- Use batch processing where possible
- Cache expensive operations
- Profile before optimizing

## Questions?

- Open an issue for questions
- Join discussions on GitHub Discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Git commit history

Thank you for contributing to PullData!
