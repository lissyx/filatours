VERSION ?= $(shell grep "version" manifest.webapp |cut -d':' -f2 |cut -d'"' -f2)
TEMPDIR ?= ../tempdir/
WEBAPP ?= filatours-$(VERSION).zip

$(info Producing $(WEBAPP))

all: $(WEBAPP)

clean: 
	rm ../$(WEBAPP) || true
	rm -rf $(TEMPDIR) || true

$(TEMPDIR):
	mkdir -p $(TEMPDIR)

webapp: $(TEMPDIR)
	cp -a * $(TEMPDIR)
	rm -rf $(TEMPDIR)/shared
	mkdir -p $(TEMPDIR)/shared
	cp -a shared/style $(TEMPDIR)/shared/
	cp -a shared/style_unstable $(TEMPDIR)/shared/
	mkdir -p  $(TEMPDIR)/shared/js
	cp -a shared/js/l10n.js shared/js/notification_helper.js $(TEMPDIR)/shared/js/

purge:
	cd $(TEMPDIR); \
	rm -rf test/; \
	rm -rf ext/font-awesome/less/ ext/font-awesome/scss/; \
	rm -rf ext/leaflet.locatecontrol/font/ ext/leaflet.locatecontrol/css/; \
	find shared/style/ -type f -name "*.html" -exec rm {} \; ; \
	find . -type f -name ".*.swp" -exec rm {} \; ;

$(WEBAPP): clean webapp purge
	cd $(TEMPDIR) && zip -r9 ../$(WEBAPP) *

.PHONY: webapp purge
