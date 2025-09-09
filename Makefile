#------------------------------------------------------------------------------#
# uv make-ing (for Python projects; just: make run)
# @docs: www.gnu.org/software/make/manual/make.txt
# @note: compliant per POSIX.1-2024, but doesn't ascend to strict divine compliance
#      : tested against pdpmake (github.com/rmyorston/pdpmake) as .POSIX is a lie
# @cred: python adaption of github.com/fetchTe/bun-make
#------------------------------------------------------------------------------#
.PRAGMA: command_comment posix_2024
.NOTPARALLEL:


#------------------------------------------------------------------------------#
# @note: sets default (make) command e.g. if 'all: build' executes 'make build' on 'make'
#------------------------------------------------------------------------------#
.PHONY: all
all: help


#------------------------------------------------------------------------------#
# @id:filepath constants
# @note: you can set the default value for any non-underscore Make constant/flag
#        via an environment variable using 'UV_MAKE_<VAR>' e.g: 'UV_MAKE_DIST=./build'
#------------------------------------------------------------------------------#
# source dir
SRC = $(CURDIR)/src/ispeak
# entrypoint
ENT = $(CURDIR)/main.py

# build/output dir
DIST = $(CURDIR)/dist
# test(s) directory
TESTS = $(CURDIR)/tests
# project root
ROOT = $(CURDIR)
# cache directories
CACHE = $(ROOT)/.pytest_cache $(ROOT)/.ruff_cache $(ROOT)/__pycache__ $(SRC)/__pycache__


#------------------------------------------------------------------------------#
# @id:flags (regardless of place/order, Make tenderly accepts all variable assignments)
#  > make PUBLISH=1 target
#  > make target PUBLISH=1
#  > PUBLISH=1 make target
#    - a shell environment variable assignment that is passed to 'make';
#      persists throughout the entire invocation, including sub/recursive ones
#------------------------------------------------------------------------------#

#: uv flags
#! [? ] uv build flag(s) (e.g: make UV="--no-build-isolation")
UV ?=

#: env flags
#! [?1] fail fast (bail) on the first test or lint error
BAIL ?= 1
#! [?0] publishes to PyPI after build (requires twine config)
PUBLISH ?= 0

#: log flags
#! [?0] enables verbose logging for tools (uv, pytest, ruff)
DEBUG ?= 0
#! [?0] disables pretty-printed/log target (INIT/DONE) info
QUIET ?= 0
#! [?0] disables color logging/ANSI codes
NO_COLOR ?= 0


#------------------------------------------------------------------------------#
# @id:extra customize-able tool flags
#------------------------------------------------------------------------------#
# ruff shared flags for linting and formatting
RUFF_FLAGS = --target-version py312
# pytest flags
PYTEST_FLAGS = -v
# pyright flags
PYRIGHT_FLAGS = --warnings
# hatch build flags
HATCH_FLAGS =
# twine upload flags
TWINE_FLAGS = --non-interactive


#------------------------------------------------------------------------------#
# @id:cross-os variable (assumes unix-y or msys2 on windows, if not, adjust accordingly)
#------------------------------------------------------------------------------#
BIN_UV = uv
BIN_UVR = uv run
BIN_HATCH = uvx hatch
BIN_TWINE = uvx twine
# required for help only; otherwise optional
_VFLG  = $$([ "$(DEBUG)" = "1" ] && echo " --verbose" || echo "")
BIN_AWK= awk
CMD_RM = rm -fr $(_VFLG)
CMD_CP = cp $(_VFLG)
CMD_MK = mkdir -p $(_VFLG)
DEVNUL = /dev/null
TMCOLS = $$(tput cols 2>$(DEVNUL) || echo 0)
# for non-GNU-y make implementations (pdpmake) that follow the POSIX standard
MKFILE = $$([ -z "$(MAKEFILE_LIST)" ] && echo "./Makefile" || echo "$(MAKEFILE_LIST)")
# GNUMAKEFLAGS is for flags that do not alter behavior, per the GNU scripture
GNUMAKEFLAGS += --no-print-directory


#------------------------------------------------------------------------------#
# @id:internal
#------------------------------------------------------------------------------#
# bail flag for pytest and tools
_BAIL = $$([ "$(BAIL)" = "1" ] && echo " -x" || echo "")
# verbose flag for tools
_VERB = $$([ "$(DEBUG)" = "1" ] && echo " -v" || echo "")


#------------------------------------------------------------------------------#
# @id::build/run
#------------------------------------------------------------------------------#
.PHONY: run
run: ## execute entry-point -> uv run main.py
	@IS_DEV=1 $(BIN_UVR) $(ENT)

.PHONY: build
build: ## build wheel/source distributions -> hatch build
	@$(MAKE) MSG="build" LEN="60" _init
	@# format check (must pass before proceeding)
	@$(MAKE) MSG="release:check" SYM="--" COLOR="1;36" _init
	@$(MAKE) BAIL="1" check || { $(MAKE) MSG="check (format/lint/type) failed..." _erro; exit 1; }
	@# run tests
	@$(MAKE) MSG="release:test" SYM="--" COLOR="1;36" _init
	@$(MAKE) test || { $(MAKE) MSG="tests failed..." _erro; exit 1; }
	@$(CMD_RM) "$(DIST)" || true
	@$(CMD_MK) "$(DIST)" || { $(MAKE) MSG="failed to create $(DIST)" _erro; exit 1; }
	@$(MAKE) _build || { $(MAKE) MSG="build failed... abort" _erro; exit 1; }
	@$(MAKE) MSG="build" LEN="60" _done

.PHONY: _build
_build: # build wrapper to provide better control and error handling
	@$(BIN_HATCH) build $(HATCH_FLAGS) $(_VFLG)

.PHONY: clean
clean: ## delete build artifacts, cache files, and temporary files
	@$(MAKE) MSG="clean" LEN="-1" _init
	@$(CMD_RM) $(DIST) $(CACHE) 2>$(DEVNUL) || true
	@find . -type d -name "*.egg-info" -exec $(CMD_RM) {} + 2>$(DEVNUL) || true
	@find . -type f -name "*.pyc" -delete 2>$(DEVNUL) || true
	@find . -type d -name "__pycache__" -exec $(CMD_RM) {} + 2>$(DEVNUL) || true
	@$(MAKE) MSG="clean" LEN="-1" _done


#------------------------------------------------------------------------------#
# @id::publish/release
#------------------------------------------------------------------------------#
.PHONY: publish
publish: ## publish to pypi.org -> twine upload
	@$(MAKE) MSG="publish" _init
	@$(BIN_TWINE) upload $(TWINE_FLAGS) $(_VFLG) $(DIST)/*
	@$(MAKE) MSG="publish" _done

.PHONY: publish_test
publish_test: ## publish to test.pypi.org -> twine upload --repository testpypi
	@$(MAKE) MSG="publish_test" _init
	@$(BIN_TWINE) upload --repository testpypi $(TWINE_FLAGS) $(_VFLG) $(DIST)/*
	@$(MAKE) MSG="publish_test" _done

.PHONY: publish_check
publish_check: ## check distributions -> twine check
	@$(MAKE) MSG="publish_check" _init
	@$(BIN_TWINE) check $(DIST)/* && \
		$(MAKE) COLOR="1;92" LEN="0" MSG="[PASS] publish_check" _pretty_printer \
		|| { $(MAKE) MSG="publish_check failed..." _erro; exit 1; }
	@$(MAKE) MSG="publish_check" _done

.PHONY:release
release: ## clean, format, lint, test, build, check, and optionally publish
	@$(MAKE) MSG="release" LEN="-1" _init
	@# clean and prepare
	@$(MAKE) MSG="release:clean" SYM="--" COLOR="1;36" _init
	@$(MAKE) clean
	@# build distributions
	@$(MAKE) MSG="release:build" SYM="--" COLOR="1;36" _init
	@$(MAKE) build
	@# check distributions
	@$(MAKE) MSG="release:publish_check" SYM="--" COLOR="1;36" _init
	@$(MAKE) publish_check || { $(MAKE) MSG="publish_check failed..." _erro; exit 1; }
	@# publish if requested
	@[ "$(PUBLISH)" = "0" ] && true || { \
		$(MAKE) MSG="release:publish" SYM="--" COLOR="1;36" _init; \
		$(MAKE) publish || { $(MAKE) MSG="publish failed..." _erro; exit 1; }; \
	}
	@$(MAKE) MSG="release" LEN="-1" _done


#------------------------------------------------------------------------------#
# @id::install/update
#------------------------------------------------------------------------------#
.PHONY: install
install: ## install dependencies -> uv sync
	@$(MAKE) MSG="install" LEN="-1" _init
	@$(BIN_UV) sync $(_VFLG) $(UV)
	@$(MAKE) MSG="install" LEN="-1" _done

.PHONY: install_cpu
install_cpu: ## install dependencies -> uv sync --extra cpu
	@$(MAKE) MSG="install_cpu" LEN="-1" _init
	@$(BIN_UV) sync --extra cpu $(_VFLG) $(UV)
	@$(MAKE) MSG="install_cpu" LEN="-1" _done

.PHONY: install_dev
install_dev: ## install dev dependencies -> uv sync --group dev --extra plugin
	@$(MAKE) MSG="install_dev" LEN="-1" _init
	@$(BIN_UV) sync --group dev --extra plugin $(_VFLG) $(UV)
	@$(MAKE) MSG="install_dev" LEN="-1" _done

install_plugin: ## install plugin dependencies -> uv sync --extra plugin
	@$(MAKE) MSG="install_plugin" LEN="-1" _init
	@$(BIN_UV) sync --extra plugin $(_VFLG) $(UV)
	@$(MAKE) MSG="install_plugin" LEN="-1" _done

.PHONY: update
update: ## update dependencies -> uv lock --upgrade && uv sync
	@$(MAKE) MSG="update" LEN="-1" _init
	@$(BIN_UV) lock --upgrade $(_VFLG)
	@$(BIN_UV) sync $(_VFLG) $(UV)
	@$(MAKE) MSG="update" LEN="-1" _done

.PHONY: update_dry
update_dry: ## show outdated dependencies  -> uv tree --outdated
	@$(BIN_UV) tree --outdated

.PHONY: venv
venv: ## setup virtual environment if needed -> uv venv -p 3.11
	@[ -n "$$VIRTUAL_ENV" ] && \
		$(MAKE) LEN="0" COLOR="1;92" MSG="[VENV] active -> $$VIRTUAL_ENV" _pretty_printer || true
	@[ -z "$$VIRTUAL_ENV" ] && [ -d ".venv" ] && \
		$(MAKE) LEN="0" COLOR="0;94" MSG="[VENV] exists" _pretty_printer || true
	@[ -z "$$VIRTUAL_ENV" ] && [ ! -d ".venv" ] && \
		$(MAKE) LEN="0" COLOR="0;33" MSG="[VENV] $(BIN_UV) venv -p 3.11" _pretty_printer && \
		$(BIN_UV) venv -p 3.11 || true
	@[ -z "$$VIRTUAL_ENV" ] && \
		$(MAKE) LEN="0" COLOR="1;37" MSG="[>RUN] source .venv/bin/activate" _pretty_printer || true


#------------------------------------------------------------------------------#
# @id::check
# @docs: docs.astral.sh/ruff
#      : microsoft.github.io/pyright
#------------------------------------------------------------------------------#
.PHONY: check
check: ## run all checks: lint, type, and format
	@$(MAKE) MSG="check" LEN="-1" _init
	@$(MAKE) lint
	@$(MAKE) type
	@$(MAKE) format
	@$(MAKE) MSG="check" LEN="-1" _done

.PHONY: format
format: ## format check -> ruff format --check
	@$(MAKE) LEN="0" MSG="format" _init
	@$(BIN_UVR) ruff format --check $(RUFF_FLAGS) $(_VERB) . && \
		$(MAKE) COLOR="1;92" LEN="0" MSG="[PASS] format" _pretty_printer \
		|| { [ "$(BAIL)" = "1" ] && $(MAKE) MSG="format failed..." _erro; exit 1; }

.PHONY: lint
lint: ## lint check -> ruff check
	@$(MAKE) LEN="0" MSG="lint" _init
	@$(BIN_UVR) ruff check $(RUFF_FLAGS) $(_VERB) $$([ "$(BAIL)" = "1" ] && echo " --exit-non-zero-on-fix" || echo "") . && \
		$(MAKE) COLOR="1;92" LEN="0" MSG="[PASS] lint" _pretty_printer \
		|| { [ "$(BAIL)" = "1" ] && $(MAKE) MSG="lint failed..." _erro; exit 1; }

.PHONY: type
type: ## type check -> pyright
	@$(MAKE) LEN="0" MSG="type" _init
	@$(BIN_UVR) pyright $(PYRIGHT_FLAGS) $(_VERB) && \
		$(MAKE) COLOR="1;92" LEN="0" MSG="[PASS] type" _pretty_printer \
		|| { [ "$(BAIL)" = "1" ] && $(MAKE) MSG="type failed..." _erro; exit 1; }

.PHONY: format_fix
format_fix: ## auto-fix format -> ruff format
	@$(MAKE) LEN="0" MSG="format_fix" _init
	@$(BIN_UVR) ruff format $(RUFF_FLAGS) $(_VERB) .
	@$(MAKE) COLOR="1;92" LEN="0" MSG="[DONE] format_fix" _pretty_printer

.PHONY: lint_fix
lint_fix: ## auto-fix lint -> ruff check --fix
	@$(MAKE) LEN="0" MSG="lint_fix" _init
	@$(BIN_UVR) ruff check --fix $(RUFF_FLAGS) $(_VERB) .
	@$(MAKE) COLOR="1;92" LEN="0" MSG="[DONE] lint_fix" _pretty_printer



#------------------------------------------------------------------------------#
# @id::test
#------------------------------------------------------------------------------#
.PHONY: test
test: ## test -> pytest
	@$(MAKE) MSG="test" _init
	@IS_TEST=1 $(BIN_UVR) pytest $(PYTEST_FLAGS) $(_BAIL) $(_VERB) $(TESTS) && \
		$(MAKE) COLOR="1;92" LEN="0" MSG="[PASS] test" _pretty_printer \
		|| { [ "$(BAIL)" = "1" ] && $(MAKE) MSG="tests failed..." _erro; exit 1; }

.PHONY: test_fast
test_fast: ## test & fail-fast -> pytest -x -q
	@$(MAKE) MSG="test_fast" _init
	@IS_TEST=1 $(BIN_UVR) pytest -x -q $(TESTS)



#------------------------------------------------------------------------------#
# @id::helpers
#------------------------------------------------------------------------------#
# color via assignment operator '!='' to execute a shell/resolve at make parse
# > CR=reset FW=fg-white-bold FD=fg-white-dim FC=fg-cyan FY=fg-yellow FB=fg-blue BW=bg-white-bold
CR != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[0m"
FW != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[1;37m"
FD != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[2;37m"
FC != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[0;36m"
FY != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[0;33m"
FB != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[0;94m"
BW != { [ "$(NO_COLOR)" = "1" ] && echo ""; } || echo "\033[1;30;47m"
NL = \n# new line (helps read-ability)
# CLI_META.version

.PHONY: help
help: ## displays (this) help screen
	@printf "$(BW)#$(CR)$(FW) USAGE$(CR) $(FD)(ispeak)$(CR)$(NL)"
	@printf "   $(FC)make$(CR) $(FY)[flags...]$(CR) $(FB)<target>$(CR)$(NL)$(NL)"
	@printf "$(BW)#$(CR)$(FW) TARGET$(CR)$(NL)"
	@$(BIN_AWK) --posix '/^# *@id::/ { printf "$(FD)  -------------------$(CR)$(NL)"  } \
	/^[A-Za-z0-9_ -]*:.*##.*$$/ { \
		target = $$1; gsub(/:.*/, "", target); \
		desc   = $$0; gsub(/^[^#]*##[[:space:]]*/, "", desc); \
		printf "   $(FB)%-22s$(CR)%s$(NL)", target, desc \
	}' $(MKFILE)
	@printf "$(NL)$(BW)#$(CR)$(FW) FLAGS$(CR)$(NL)"
	@$(BIN_AWK) --posix '/^#: / { printf "$(FD)  -------------------$(CR)$(NL)"  } \
	/^#!/ { comment = substr($$0, 3); } \
	comment && /^[a-zA-Z][a-zA-Z0-9_-]+ ?\?=/ { \
		printf "   $(FY)%-21s$(CR)%s$(NL)", $$1, comment; \
	}' $(MKFILE)

.PHONY: _pretty_printer
_pretty_printer: # pretty printer (tr, could be better opt, need to look at os support)
	@LEN=$${LEN:-46}; \
	[ "$${QUIET:-0}" -ne 0 ] && exit 0; \
	[ "$$LEN" -eq -1 ] && LEN=$(TMCOLS); \
	[ "$(TMCOLS)" -eq 0 ] && LEN=0; \
	CC="$$([ "$(NO_COLOR)" = "1" ] && echo "" || echo "\033[$${COLOR:-34}m")"; \
	CL=$$(i=0; while [ $$i -lt $$LEN ]; do printf "%s" "$${SYM:--}"; i=$$((i+1)); done); \
	LL=$$([ "$$LEN" -ne 0 ] && echo "$(NL)" || echo ""); \
	printf "$${LL}$${CC}%s$(CR)$${LL}$${CC}%s$(CR)$${LL}$${CC}%s$(CR)$(NL)" "$${CL}" "$(MSG)" "$${CL}";
.PHONY: _erro
_erro:
	@$(MAKE) COLOR="1;31" MSG="[ERRO] $(MSG)" SYM="*" LEN="-1" _pretty_printer
.PHONY: _init
_init:
	@$(MAKE) MSG="[INIT] $(MSG)" _pretty_printer
.PHONY: _done
_done:
	@$(MAKE) COLOR="1;92" MSG="[DONE] $(MSG)" _pretty_printer
