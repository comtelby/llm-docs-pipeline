# opencode project configuration

## Commands
- Tests: `pytest tests/ -v`
- Lint: `ruff check src/ --ignore=E501`
- Typecheck: `mypy src/ --ignore-missing-imports`
- Run dev: `uvicorn src.main:app --reload --port 8000`
- Build: `docker build -t llm-docs-pipeline-fastapi-bot .`
- Docker compose: `docker-compose up -d`

## Code style
- Line length: 120
- Quotes: double
- No comments unless necessary
- Type hints: use `Optional`, `list`, `dict` from typing
- Naming: snake_case for functions/vars, PascalCase for classes
- Imports: standard lib → third-party → local, groups separated by blank line
- Error handling: log with `logger.warning` for non-critical, raise HTTPException for API errors
- Async: use `asyncio.to_thread()` for blocking calls, `aiofiles` for file I/O
