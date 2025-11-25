# Contributing Guidelines

> Comprehensive guide for developers contributing to the Prodloop Task Management API

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Conventions](#commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Standards](#documentation-standards)

---

## 🤝 Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Docker (for testing deployments)
- Google Cloud account (for deployment)

### Fork & Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/prodloop_task_project.git
cd prodloop_task_project

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/prodloop_task_project.git
```

---

## 🛠️ Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 4. Start Development Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 5. Verify Installation

```bash
# Test API health
curl http://localhost:8080/health

# View Swagger UI
# Open: http://localhost:8080/docs
```

---

## 💻 Coding Standards

### Style Guide

We follow **PEP 8** with these specifications:

```python
# Code formatting: 4 spaces indentation
def create_task(task: TaskCreate) -> Task:
    """Create a new task.
    
    Args:
        task: Task creation payload
        
    Returns:
        Created task with ID and timestamp
        
    Raises:
        HTTPException: If validation fails
    """
    pass


# Line length: 88 characters (Black formatter default)
# Max line length: 100 characters for code, 79 for comments


# Naming conventions
class TaskModel:           # PascalCase for classes
    def create_task(self): # snake_case for methods/functions
        task_id = "uuid"   # snake_case for variables
        MAX_RETRIES = 3    # UPPER_CASE for constants
```

### Type Hints

Always use type hints:

```python
# Good
def list_tasks(priority: Optional[str] = None, 
               status: Optional[str] = None) -> List[Task]:
    tasks: List[Task] = []
    return tasks


# Avoid
def list_tasks(priority=None, status=None):
    tasks = []
    return tasks
```

### Docstrings

Use Google-style docstrings:

```python
def get_task(task_id: str) -> Task:
    """Retrieve a specific task by ID.
    
    Fetches a task from the in-memory store and returns its details.
    Returns 404 error if task doesn't exist.
    
    Args:
        task_id: Unique identifier of the task (UUID format)
        
    Returns:
        Task: Task object with all details
        
    Raises:
        HTTPException: 404 if task not found
        
    Example:
        >>> task = get_task("550e8400-e29b-41d4-a716-446655440000")
        >>> print(task.title)
        "Fix auth bug"
    """
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

### Error Handling

```python
# Good: Specific error handling
try:
    publisher = pubsub_v1.PublisherClient()
    future = publisher.publish(topic_path, data=data)
    result = future.result(timeout=10)
except TimeoutError:
    logger.error(f"Pub/Sub publish timeout for task {task_id}")
    # Fall back to file logging
except Exception as e:
    logger.error(f"Pub/Sub publish failed: {str(e)}")
    # Graceful degradation


# Avoid: Bare except clauses
try:
    pass
except:  # Never do this
    pass
```

### Imports

```python
# Order: Standard library, third-party, local
import os
import json
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import Task, TaskCreate
```

---

## 📝 Commit Conventions

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without feature/bug changes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

### Scope

- `api`: REST API changes
- `pubsub`: Pub/Sub integration
- `gemini`: Gemini integration
- `docker`: Docker/container changes
- `ci`: GitHub Actions CI/CD
- `docs`: Documentation changes

### Subject

- Use imperative mood ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at end
- Maximum 50 characters

### Examples

```
feat(api): add task filtering by status

fix(pubsub): handle missing topic path gracefully

docs(deployment): add Cloud Run setup instructions

refactor(gemini): extract API call logic to helper method

test(api): add comprehensive endpoint tests

chore(deps): update fastapi to 0.105.0
```

---

## 🔄 Pull Request Process

### 1. Create Feature Branch

```bash
# Update main branch
git fetch upstream
git checkout upstream/main

# Create feature branch
git checkout -b feat/short-description
# or
git checkout -b fix/short-description
```

### 2. Make Changes

- Keep commits atomic and logical
- Write clear commit messages
- Add tests for new features
- Update documentation

### 3. Push to Fork

```bash
git push origin feat/short-description
```

### 4. Create Pull Request

On GitHub:
- Add descriptive title
- Reference related issues (#123)
- Add PR description using template
- Link to relevant documentation

### PR Template

```markdown
## Description
Brief description of changes

## Related Issues
Closes #123

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Added unit tests
- [ ] All tests passing

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tested on main branch
```

### 5. Code Review

- Address all review comments
- Push additional commits
- Request re-review when ready

### 6. Merge

Maintain clean history:
```bash
# Use "Squash and merge" for feature branches
# Use "Create a merge commit" for release branches
```

---

## 🧪 Testing Guidelines

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTaskEndpoints:
    """Test task management endpoints."""
    
    def test_create_task_success(self):
        """Test successful task creation."""
        payload = {
            "title": "Test Task",
            "description": "Test Description",
            "priority": "high"
        }
        response = client.post("/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_task_validation_error(self):
        """Test task creation with invalid priority."""
        payload = {
            "title": "Test Task",
            "priority": "invalid"
        }
        response = client.post("/tasks", json=payload)
        
        assert response.status_code == 422
    
    def test_get_nonexistent_task(self):
        """Test retrieving non-existent task."""
        response = client.get("/tasks/nonexistent-id")
        assert response.status_code == 404
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_api.py

# Run with coverage
pytest --cov=app test_api.py

# Run in verbose mode
pytest -v

# Run specific test
pytest test_api.py::TestTaskEndpoints::test_create_task_success
```

### Test Coverage

- Aim for >80% code coverage
- Test all error paths
- Test edge cases
- Test integration points

---

## 📚 Documentation Standards

### Code Documentation

Every module, class, and function should have:

```python
"""Module docstring describing the module's purpose.

This module contains task management routes and handles
all CRUD operations for tasks.

Example:
    >>> from app.routes import tasks
    >>> router = tasks.router
"""

class Task(BaseModel):
    """Represents a task in the system.
    
    Attributes:
        id: Unique identifier (UUID)
        title: Task title
        description: Optional task description
        priority: Task priority (low, medium, high)
        status: Current task status
        created_at: Creation timestamp
    """
    pass
```

### README Standards

- Keep updated with major changes
- Include quick start section
- Document all endpoints
- Provide examples
- Link to detailed documentation

### API Documentation

- Use FastAPI decorators for descriptions
- Include example payloads
- Document all status codes
- Explain error responses

```python
@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(payload: TaskCreate):
    """Create a new task.
    
    Create a new task with the provided title, description, and priority.
    The system automatically generates a unique ID and timestamp.
    
    Upon successful creation, publishes a 'task.created' event to Pub/Sub.
    
    Args:
        payload: Task creation payload
        
    Returns:
        Created task with auto-generated ID and timestamp
        
    Raises:
        422: If request validation fails
        500: If Pub/Sub publishing fails
    """
    pass
```

---

## 🔍 Code Review Checklist

When reviewing code, ensure:

- [ ] Follows coding standards
- [ ] Has appropriate type hints
- [ ] Includes docstrings
- [ ] Error handling is comprehensive
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded secrets
- [ ] Performance is acceptable
- [ ] Security concerns addressed
- [ ] Commit messages are clear

---

## 🚀 Performance Guidelines

### API Performance

- Target: < 100ms response time
- Measure with: `curl -w "@curl_format.txt" <url>`
- Optimize slow queries (> 1s)

### Memory Usage

- Monitor: Use `memory_profiler`
- Target: < 100MB per request
- Profile: `python -m memory_profiler script.py`

### Code Optimization

```python
# Avoid: N+1 queries
for task_id in task_ids:
    task = TASK_STORE.get(task_id)  # Called N times

# Better: Batch operations
tasks = [TASK_STORE.get(tid) for tid in task_ids if tid in TASK_STORE]

# Avoid: Unnecessary copying
new_list = list(tasks)

# Better: Use iterators
for task in tasks:
    process(task)
```

---

## 🔐 Security Guidelines

### Secret Handling

```python
# Good: Use environment variables
api_key = os.getenv("GEMINI_API_KEY")

# Avoid: Hardcoded secrets
api_key = "sk_live_xxx"  # Never do this!
```

### Input Validation

```python
# Good: Validate all inputs
@router.post("/tasks")
async def create_task(payload: TaskCreate):
    # Pydantic automatically validates

# Avoid: Trusting user input
@router.post("/tasks")
async def create_task(data: dict):
    # No validation, dangerous!
```

### Error Messages

```python
# Good: Generic error messages
raise HTTPException(status_code=404, detail="Task not found")

# Avoid: Revealing sensitive information
raise HTTPException(status_code=500, 
    detail=f"Database connection failed: {e.connection_string}")
```

---

## 📞 Getting Help

- Check existing issues and discussions
- Ask questions in pull requests
- Review documentation
- Contact maintainers

---

## 📋 Changelog

Document changes in `CHANGELOG.md`:

```
## [1.1.0] - 2025-01-15

### Added
- Task filtering by status
- Gemini integration for task analysis

### Fixed
- Handle missing Pub/Sub configuration

### Changed
- Updated error messages for clarity

### Deprecated
- Legacy API endpoints (use /tasks instead)

### Removed
- Unused utility functions

### Security
- Updated dependencies for security patches
```

---

## 🎯 Development Workflow

1. **Create branch** from latest main
2. **Make changes** following guidelines
3. **Write tests** for new features
4. **Update docs** as needed
5. **Commit with** clear messages
6. **Push to fork** and create PR
7. **Respond to** review comments
8. **Squash and merge** when approved

---

## 📊 Contribution Stats

Track contributions:
- Issues resolved
- PRs merged
- Tests added
- Documentation improved

---

## ✨ Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- GitHub contributors page

---

Thank you for contributing to making Prodloop better! 🚀
