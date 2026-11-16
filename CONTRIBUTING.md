# Contributing

Thanks for your interest in improving the Semantic Intent Search Engine. Bug reports,
feature ideas and pull requests are welcome.

## Reporting bugs and requesting features

Use the issue templates on GitHub (**Issues → New issue**). For bugs, include what you did,
what you expected, what happened, and your OS / Python / Node versions.

Security problems should be reported privately — see [SECURITY.md](SECURITY.md).

## Development setup

Follow the [installation guide](README.md#installation), then install the test tools:

```bash
pip install -r requirements-dev.txt
cd semantic-search-frontend && npm install
```

## Before opening a pull request

```bash
python -m pytest                       # backend tests
cd semantic-search-frontend
npm run lint                           # frontend lint
npm run build                          # frontend build
```

If you change retrieval, intent detection or confidence thresholds, also run the evaluation
and include the numbers in your pull request:

```bash
python -m scripts.evaluate_intent
python -m scripts.evaluate_pipeline --full
```

## Guidelines

- Keep pull requests focused on one change and describe *why* it is needed.
- Add or update tests for behaviour changes.
- Follow the existing code style (see `.editorconfig`); the frontend is checked by ESLint.
- Never commit `.env`, credentials, customer documents or generated data.
- Auto-reply precision must not drop: the system must never send answers it cannot support.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
