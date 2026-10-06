# Contributing

Run `make test` (backend unittest + frontend library tests and type check) before opening a PR. Keep new providers behind the interfaces in
`app/providers/base.py`, put business logic in `app/services`, and never add a feature that returns made-up data: missing values must read "Not reported" / "Not evaluated".
