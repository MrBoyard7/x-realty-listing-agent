# Contributing

Thanks for considering a contribution!

## Development setup

```bash
git clone https://github.com/MrBoyard7/x-realty-listing-agent.git
cd x-realty-listing-agent
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install  # optional, but recommended
```

## Running checks locally

```bash
black src tests            # auto-format
flake8 src tests            # lint
mypy src                    # type-check
pytest                       # unit tests + coverage
```

All four must pass before opening a pull request; the same checks run in CI
(see `.github/workflows/ci.yml`).

## Code style

- Format with `black` (line length 100, see `pyproject.toml`).
- All code, comments, and docstrings are written in English.
- Prefer small, focused functions with type hints and a short docstring
  explaining *why*, not just *what*.
- New behavior should ship with tests in `tests/`.

## Commit messages

Use short, imperative subject lines (e.g. `Add RedFin URL builder`,
`Fix address regex greediness`).

## Reporting issues

Please open a GitHub issue with steps to reproduce, expected behavior, and
actual behavior. For anything touching the X API or Microsoft Graph
integration, include the relevant (sanitized) response payload if possible.
