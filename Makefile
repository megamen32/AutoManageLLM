ROOT     = $(shell pwd)
VENV     = $(ROOT)/.venv
PYTHON   = $(VENV)/bin/python
PIDFILE  = /tmp/multimanager.pid
LOGFILE  = /tmp/multimanager.log

.PHONY: restart build stop start status logs clean

build:
	uv sync

start: build
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "[mm] already running (PID $$(cat $(PIDFILE)))"; exit 0; \
	fi
	@echo "[mm] starting..."
	@nohup $(PYTHON) $(ROOT)/app.py > $(LOGFILE) 2>&1 & PID=$$!; echo $$PID > $(PIDFILE)
	@sleep 2
	@if kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "[mm] started (PID $$(cat $(PIDFILE)))"; \
	else \
		echo "[mm] failed to start, see $(LOGFILE)"; cat $(LOGFILE); rm -f $(PIDFILE); exit 1; \
	fi

stop:
	@if [ -f $(PIDFILE) ]; then \
		kill $$(cat $(PIDFILE)) 2>/dev/null; rm -f $(PIDFILE); \
	fi
	@pkill -f "app.py" 2>/dev/null; true
	@echo "[mm] stopped"

restart: stop start

status:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "[mm] running (PID $$(cat $(PIDFILE)))"; \
	else \
		echo "[mm] not running"; \
	fi

logs:
	@if [ -f $(LOGFILE) ]; then cat $(LOGFILE); else echo "[mm] no log file"; fi

clean:
	rm -rf $(VENV) __pycache__ multimanager/__pycache__
	rm -rf .pytest_cache *.egg-info
	rm -f $(PIDFILE) $(LOGFILE)
