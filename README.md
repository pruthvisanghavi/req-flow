# req-flow

Requirements go in. Tests flow out.

AI-powered test generation using a local Qwen LLM (via Ollama).

## How it works

```
requirements/requirements.txt  →  generate_test.py  →  Ollama/Qwen
        +                                                    ↓
   src/<class>.py          traceability check         tests/test_<class>.py
                                                            ↓
                                                       pytest + coverage
```

## File structure

```
req-flow/
├── requirements/
│   └── requirements.txt     ← one line per requirement
├── src/
│   └── <class>.py           ← classes under test (you write these)
├── tests/                   ← generated tests (created at runtime)
├── reports/                 ← coverage HTML report
├── prompt.txt               ← LLM instructions
├── generate_test.py         ← the pipeline
├── pytest.ini               ← coverage config
├── Dockerfile
├── Dockerfile.ollama
├── docker-compose.yml
└── start-ollama.sh
```

## Requirements format

```
REQ-001 | estop   | The robot shall stop within 100ms of an emergency stop signal.
REQ-002 | battery | The robot shall warn when battery drops below 20%.
```

Pipe-separated: `ID | class_name | description`
`class_name` must match a file in `src/`.

## Run

```bash
# Start Ollama (first time pulls the model automatically)
docker compose up ollama -d

# Generate tests for all requirements
docker compose run --rm -it pipeline

# Run tests + coverage report
pytest tests/ -v

# Open coverage report
open reports/coverage/index.html
```

## Add a new requirement

1. Add a line to `requirements/requirements.txt`
2. Drop the class in `src/<class_name>.py`
3. Re-run `docker compose run --rm -it pipeline`
