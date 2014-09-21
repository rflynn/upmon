
SQLITE3 := sqlite3
PIP := pip

test: FORCE

init: FORCE
	$(SQLITE3) upmon.sqlite3 < schema.sql
	$(PIP) install -r requirements.txt

FORCE:
