# dmclient Makefile
# Copyright (C) 2017 Alex Mair. All rights reserved.
# This file is part of dmclient.
#
# dmclient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# dmclient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dmclient.  If not, see <http://www.gnu.org/licenses/>.
#

MAKEFLAGS += -Rr --no-print-directory
PHONY=
.SUFFIXES:
all:
Makefile: ;

ifeq ("$(origin V)", "command line")
  VERBOSE=$(V)
endif
ifndef VERBOSE
  VERBOSE=0
endif

ifeq ($(VERBOSE),1)
  craptools_hack=
  quiet=
  Q=
else
  craptools_hack=>/dev/null
  quiet=quiet_
  Q=@
endif


# Recipe configuration

PYUIC=pyuic5
PYUICFLAGS=

PYRC=pyrcc5
PYRCFLAGS=

SPHINX=sphinx


# Cmds and variables.
#

cmd_pyuic               =                      \
	$(PYUIC) $(PYUICFLAGS) -o $@ $< ;      \
	sed -e 's/import icons_rc//' -i -- "$@"
quiet_cmd_pyuic         = PYUIC    $@

cmd_pyrc                = $(PYRC) $(PYRCFLAGS) -o $@ $<
quiet_cmd_pyrc          = PYRC     $@

cmd_pkg_archive=                   \
	set -e ;                   \
	cd $< ;                    \
	find . -name '.*' -delete ;\
	export COPYFILE_DISABLE=1 ;\
	tar cjf $(notdir $@) * ;   \
	mv $(notdir $@) ..
quiet_cmd_pkg_archive=PACKAGE  $@

# This is dumb.
cmd_gendocs    =                               \
	sphinx-apidoc -o doc/src . ui/widgets ;\
	mkdir doc/html 2>/dev/null            ;\
	sphinx-build -b html doc/ doc/html
quiet_cmd_gendocs=GENDOCS  doc/


# Input files
#

# FIXME: hack
ui_files_:=$(shell find resources/qt -name '*.ui' | sed -e 's/resources\/qt/ui\/widgets/')
ui_dirs=$(filter-out ui/widgets/,$(sort $(dir $(ui_files_))))
ui_dirinit=$(addsuffix /__init__.py,$(ui_dirs))
ui_files=$(ui_files_:.ui=.py)

test_archives=resources/test/protege/testcampaign.dmc \
	      resources/test/protege/testlibrary.dml \
	      resources/test/badmeta.dmc


# Primary targets.
#

PHONY+=help
help:
	@echo dmclient\'s Makefile supports the following:
	@echo "    all"
	@echo "    docs"
	@echo "    qrc"
	@echo "    tests"
	@echo "    testarchives"
	@echo "    ui"
	@echo "    clean"
	@echo "    clean-docs"
	@echo "    clean-pycache"
	@echo "    clean-resources"
	@echo "    clean-ui"

PHONY+=all
all: testarchives qrc ui

PHONY+=docs
docs: FORCE
	$(call if_dep_changed,gendocs)

PHONY+=qrc
qrc: ui/widgets/icons_rc.py
ui/widgets/icons_rc.py: resources/icons.qrc

PHONY+=tests
tests:
	py.test

PHONY+=testarchives
testarchives: $(test_archives)

PHONY+=ui
ui: $(ui_files)
$(ui_files): $(ui_dirinit)
$(ui_dirinit): $(ui_dirs)

PHONY+=clean $(sub_clean)
sub_clean = clean-docs clean-pycache clean-resources clean-ui
clean: $(sub_clean)

clean-docs:
	$(RM) -r doc/html doc/src

clean-pycache:
	find . -name __pycache__ | xargs $(RM) -r

clean-resources: clean-testarchives
	$(RM) ui/widgets/icons_rc.py

clean-testarchives:
	$(RM) $(test_archives)

clean-ui:
	find ui/widgets \( -not -wholename ui/widgets -and -not -wholename ui/widgets/__init__.py \) -delete


# General targets
#

ui/widgets/%.py: resources/qt/%.ui
	$(call if_dep_changed,pyuic)

ui/widgets/%_rc.py: resources/%.qrc
	$(call if_dep_changed,pyrc)

# Hack
%/__init__.py: ;

# FIXME: cmd?
ui/widgets/%/:
	mkdir $@ ;           \
	touch $@/__init__.py

# FIXME these should not be FORCE.
%.dmc: % FORCE
	$(call if_dep_changed,pkg_archive)

%.dml: % FORCE
	$(call if_dep_changed,pkg_archive)


# "Internal" magic and guts.
#

echo_cmd = $(if $($(quiet)cmd_$(1)),     \
        echo "  $($(quiet)cmd_$(1))";)

prereqs=$(filter-out $(PHONY),$?)
if_dep_changed=$(if $(strip $(prereqs)),  \
	@set -e;                          \
	$(echo_cmd) $(cmd_$(1)))

.PHONY: $(PHONY)
.PHONY: FORCE
FORCE: ;
