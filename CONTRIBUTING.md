# Contributing

Thanks for your interest in contributing. This is a small research/prototype
project, so the bar for contributions is low but the honesty bar is high.

## Ground rules

- **Do not fabricate results.** Metrics (accuracy, MRR, latency) must come from
  running the code, not from hand-written claims. If a number is a rough
  estimate, label it as such.
- **Keep the architecture.** Prefer small, focused changes to the existing
  module layout over a ground-up rewrite, unless a rewrite is explicitly
  justified.
- **Keep failure cases.** Do not delete or "fix" a test case merely to raise
  accuracy; document why a case is hard instead.
- **Do not fabricate data.** The resource library is a curated subset of a
  public pricing quota. Do not invent materials, specifications, or prices.

## Development setup

```bash
python -m venv .venv
# activate the venv for your shell, then:
pip install -r requirements.txt
python -m pytest            # run the test suite
python main.py --report     # run the evaluation suite
python main.py --ablation   # run the ablation study
```

## Making changes

1. Open an issue describing the change (or comment on an existing one).
2. Create a branch from `main`.
3. Add or update tests in `tests/` for any behavior change.
4. Run `python -m pytest` and `python main.py --report` before pushing.
5. Keep the README and CHANGELOG in sync with user-visible changes.

## Data provenance

The bundled library's source and the integrity check (`validate_db`) are
documented in `data/data_source.md`. If you add or modify resource entries,
update that file and keep `validate_db()` clean.

## License

By contributing you agree that your work is licensed under the project's MIT
license.
