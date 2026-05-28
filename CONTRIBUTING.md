# Contributing Guide

Thanks for contributing to `personal_me`.

## Branch Naming (Git Flow)

Use short-lived branches from `main`:

- `feature/<scope>-<short-description>`
- `fix/<scope>-<short-description>`
- `docs/<scope>-<short-description>`
- `chore/<scope>-<short-description>`

Examples:

- `feature/backend-terminal-executor`
- `fix/frontend-command-history`
- `docs/readme-api-section`

## Commit Message Standard (Conventional Commits)

Format:

```text
<type>(<scope>): <subject>
```

Main types:

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation update
- `chore`: maintenance or tooling

Examples:

- `feat(backend): add terminal command execute endpoint`
- `fix(frontend): improve arrow history navigation`
- `docs(root): document docker quickstart`

## Code Requirements

### Python / FastAPI

- Use Python 3.11+.
- Type hints are required for public functions and methods.
- Use Google Style docstrings for functions and methods.
- Every API endpoint must include `summary` and `description` for Swagger UI.

Google Style docstring example:

```python
def create_access_token(subject: str) -> str:
    """Create JWT token.

    Args:
        subject: Username stored in token payload.

    Returns:
        Signed JWT token.
    """
```

### TypeScript / Nuxt 3

- Strict TypeScript is required (`strict: true`).
- Avoid `any` unless there is a clear technical reason.
- Nuxt components must include short JSDoc for props and core logic.

## Pull Request Checklist

- [ ] Branch naming follows this guide.
- [ ] Commits follow Conventional Commits.
- [ ] New backend endpoints include Swagger `summary` and `description`.
- [ ] Type hints / TypeScript typing are present.
- [ ] JSDoc added for new Nuxt component props or logic.
- [ ] Docs (`README.md` or `docs/*`) updated if behavior changed.

