
SQLITE3 := sqlite3
PIP := pip

test: FORCE

init: FORCE
	$(SQLITE3) upmon.sqlite3 < schema.sql
	sudo $(PIP) install -r requirements.txt
	sudo mkdir -p /opt
	sudo ln -s $(pwd) /opt/upmon

FORCE:
