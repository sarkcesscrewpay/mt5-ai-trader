# Contributing to MCP MetaTrader 5 Server

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- MetaTrader 5 terminal (for integration testing)
- Git

### Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/mcp-metatrader5-server.git
cd mcp-metatrader5-server
```

2. **Install dependencies**

```bash
# Install all dependencies including dev and docs
uv sync --all-extras
```

3. **Set up environment**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your MT5 configuration
```

4. **Run tests to verify setup**

```bash
uv run pytest -m unit
```

## Development Workflow

### Creating a Branch

```bash
# Create a new branch for your feature or fix
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### Making Changes

1. Make your changes in the appropriate files
2. Add tests for new functionality
3. Update documentation if needed
4. Run tests to ensure everything works

### Running Tests

```bash
# Run all unit tests
uv run pytest -m unit

# Run with coverage
uv run pytest --cov=mcp_mt5 --cov-report=html

# Run specific test file
uv run pytest tests/test_timeframes.py -v

# Run linting
uvx ruff check src/ tests/
uvx ruff format src/ tests/
```

### Code Style

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check code style
uvx ruff check src/ tests/

# Format code
uvx ruff format src/ tests/

# Fix auto-fixable issues
uvx ruff check --fix src/ tests/
```

### Writing Tests

- Place tests in the `tests/` directory
- Use the `@pytest.mark.unit` marker for unit tests
- Use the `@pytest.mark.integration` marker for tests requiring MT5
- Follow the FastMCP testing patterns (see `tests/README.md`)

Example test:

```python
import pytest
from fastmcp import Client
from mcp_mt5.main import mcp

@pytest.mark.unit
async def test_my_feature():
    """Test description."""
    async with Client(mcp) as client:
        result = await client.call_tool("my_tool", {"param": "value"})
        assert result.data == expected_value
```

### Documentation

- Update docstrings for any new or modified functions
- Update `docs/` if adding new features
- Update `README.md` if changing installation or usage

Build docs locally:

```bash
uv run mkdocs serve
# Visit http://127.0.0.1:8000
```

## Submitting Changes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `ci:` CI/CD changes
- `chore:` Maintenance tasks

Examples:

```bash
git commit -m "feat: add support for custom timeframes"
git commit -m "fix: handle MT5 connection timeout"
git commit -m "docs: update installation instructions"
git commit -m "test: add tests for order validation"
```

### Creating a Pull Request

1. **Push your branch**

```bash
git push origin feature/your-feature-name
```

2. **Create a Pull Request on GitHub**

- Go to the repository on GitHub
- Click "New Pull Request"
- Select your branch
- Fill out the PR template
- Link any related issues

3. **Wait for Review**

- CI tests will run automatically
- Address any feedback from reviewers
- Make additional commits if needed

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Code follows project style
- [ ] Commit messages follow conventions
- [ ] PR description is clear and complete

## Types of Contributions

### Bug Reports

- Use the bug report template
- Include steps to reproduce
- Provide error messages and logs
- Specify your environment details

### Feature Requests

- Use the feature request template
- Explain the use case
- Describe the proposed solution
- Consider implementation details

### Code Contributions

- Fix bugs
- Add new features
- Improve performance
- Enhance documentation
- Add tests

### Documentation

- Fix typos or unclear explanations
- Add examples
- Improve API documentation
- Write tutorials or guides

## Code Review Process

1. **Automated Checks**
   - CI tests must pass
   - Code coverage should not decrease significantly
   - Linting checks must pass

2. **Manual Review**
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Breaking changes consideration

3. **Approval and Merge**
   - At least one approval required
   - All conversations resolved
   - CI passing
   - No merge conflicts

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push tag to trigger release workflow
5. GitHub Actions publishes to PyPI

## Getting Help

- 📚 [Documentation](https://mcp-metatrader5-server.readthedocs.io)
- 💬 [GitHub Discussions](https://github.com/Qoyyuum/mcp-metatrader5-server/discussions)
- 🐛 [Issue Tracker](https://github.com/Qoyyuum/mcp-metatrader5-server/issues)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub's [Community Guidelines](https://docs.github.com/en/site-policy/github-terms/github-community-guidelines)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or start a discussion if you have any questions!
