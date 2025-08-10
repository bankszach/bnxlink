# Contributing to BNX Link

Thank you for your interest in contributing to BNX Link! This document provides guidelines and information for contributors.

## Quick Start

1. **Fork** the repository
2. **Branch** from `main` with a descriptive name
3. **Develop** your changes with focused commits
4. **Test** your changes thoroughly
5. **Submit** a pull request

## Development Setup

### Prerequisites
- Python 3.11+
- `make` utility
- Git

### Local Setup
```bash
# Clone and setup
git clone https://github.com/bnxlink/bnxlink.git
cd bnxlink
make venv install

# Run the demo to verify setup
make demo
```

### Common Development Tasks
```bash
make objects       # Hash and store sample objects
make manifest      # Build manifest
make promote       # Promote manifest to staging/prod
make validate      # Validate repository integrity
make db            # Rebuild DuckDB projection
make agent         # Run console agent
make api           # Start API server
```

## Testing

### Run Tests
```bash
# Run all tests
pytest -q

# Run specific test file
pytest tests/test_smoke.py

# Run with coverage
pytest --cov=bnxlink
```

### Test Guidelines
- Write tests for new functionality
- Ensure existing tests pass
- Aim for high test coverage
- Test both success and error cases

## Code Quality

### Commit Guidelines
- **Small, focused commits** - one logical change per commit
- **Descriptive commit messages** - explain what and why, not how
- **Sign-off requirement** - add `Signed-off-by: Your Name <you@example.com>` to each commit

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for public functions and classes
- Keep functions focused and readable

### Pull Request Guidelines
- **Scope labels**: Use appropriate labels (feat, fix, chore, docs, test, refactor)
- **Description**: Clear description of changes and rationale
- **Testing**: Describe how you tested your changes
- **Breaking changes**: Note any breaking changes clearly

## Documentation

### Documentation Structure
- **README.md**: Project overview and quickstart
- **docs/architecture.md**: System architecture and design
- **docs/data-model.md**: Data structures and schemas
- **docs/roadmap.md**: Future development plans
- **docs/security.md**: Security model and practices

### Contributing to Documentation
- Keep documentation up-to-date with code changes
- Add examples for new features
- Update diagrams and schemas as needed
- Ensure links and references are correct

## Project Structure

```
bnxlink/
├── agent/          # Console agent and CLI tools
├── api/            # FastAPI server and endpoints
├── data/           # Data storage and samples
├── docs/           # Documentation
├── schemas/        # JSON Schema definitions
├── scripts/        # Utility scripts
└── tests/          # Test suite
```

## Areas for Contribution

### High Priority
- **Testing**: Expand test coverage and add integration tests
- **Documentation**: Improve guides and add examples
- **Performance**: Optimize data processing and API responses
- **Security**: Enhance authentication and access controls

### Medium Priority
- **API Features**: Add new endpoints and functionality
- **Agent Tools**: Enhance CLI capabilities
- **Data Validation**: Improve schema validation and error handling
- **Monitoring**: Add metrics and observability

### Low Priority
- **Integration**: Third-party service connectors
- **UI Tools**: Web-based management interface
- **Analytics**: Advanced querying and reporting
- **Deployment**: Container and cloud deployment guides

## Getting Help

### Resources
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check existing docs first
- **Code**: Review source code for examples

### Communication
- Be respectful and inclusive
- Ask questions when unsure
- Provide context for issues
- Help others when possible

## Legal

### Contributor License Agreement
By contributing to BNX Link, you agree that your contributions will be licensed under the Apache License 2.0.

### Sign-off Requirement
This project uses the Developer Certificate of Origin (DCO). Each commit must include:
```
Signed-off-by: Your Name <you@example.com>
```

You can add this automatically with:
```bash
git commit -s -m "Your commit message"
```

## Recognition

Contributors will be recognized in:
- **Contributors list** on GitHub
- **Release notes** for significant contributions
- **Documentation** for major features
- **Community acknowledgments**

## Questions?

If you have questions about contributing:
1. Check the [documentation](docs/) first
2. Search existing [issues](https://github.com/bnxlink/bnxlink/issues)
3. Start a [discussion](https://github.com/bnxlink/bnxlink/discussions)
4. Contact the maintainers directly

Thank you for contributing to BNX Link!


