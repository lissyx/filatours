TEMPDIR ?= ../tempdir/
WEBAPP ?= filatours.zip

all: $(WEBAPP)

clean: 
	rm -rf $(TEMPDIR)

$(TEMPDIR): clean
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

$(WEBAPP): webapp purge
	cd $(TEMPDIR) && zip -r9 ../$(WEBAPP) *

.PHONY: webapp purge
