scriptname=pulseox-bluetooth.py
editfiles=Makefile \
		  $(scriptname) \
		  remotedisplay.py \
		  settings.py \
		  alerts.py \
		  utils.py \
		  plotdisp.py \
		  ovals.py \
		  flogging.py \
		  usercallbacks.py \
		  usercallbacks-example.py \
		  bansi.py \
		  settings-sample.py README.md

all:
	@echo 'Commands:'
	@echo '  make vi    (edit files with vim)'
	@echo '  make edit  (edit files using $$EDITOR)'
	@echo '  make run   (run pulseox-bluetooth.py)'

run:
	./$(scriptname)

edit:
	@echo
	@echo "Using editor: $(EDITOR)"
	@sleep 2
	"$(EDITOR)" $(editfiles)

vi:
	vim $(editfiles)
