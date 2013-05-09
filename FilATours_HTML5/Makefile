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
	rm $(TEMPDIR)/shared
	mkdir -p $(TEMPDIR)/shared
	cp -a shared/style $(TEMPDIR)/shared/
	cp -a shared/style_unstable $(TEMPDIR)/shared/

purge:
	cd $(TEMPDIR); \
	rm -f ext/OpenLayers/*.debug.js; \
	rm -rf ext/OpenLayers/lib/Firebug/; \
	rm -rf test/; \
	find shared/style/ -type f -name "*.html" -exec rm {} \; ; \
	find . -type f -name ".*.swp" -exec rm {} \; ;

$(WEBAPP): clean webapp purge
	cd $(TEMPDIR) && zip -r9 ../$(WEBAPP) *

.PHONY: webapp purge
