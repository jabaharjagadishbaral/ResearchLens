test:
	cd frontend && node --test lib/lib.test.ts && tsc -p tsconfig.lib.json
	cd backend && python -m unittest discover -s tests -v
eval:
	python evaluation/run_eval.py
