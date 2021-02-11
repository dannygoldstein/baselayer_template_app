.DEFAULT_GOAL = help

baselayer/Makefile:
	git submodule update --init --remote

# https://www.gnu.org/software/make/manual/html_node/Overriding-Makefiles.html
%: baselayer/Makefile force
	@$(MAKE) --no-print-directory -C . -f baselayer/Makefile $@

.PHONY: Makefile force

api-docs: FLAGS := $(if $(FLAGS),$(FLAGS),--config=config.yaml)
api-docs: | dependencies
	@PYTHONPATH=. python tools/openapi/build-spec.py $(FLAGS)
	npx redoc-cli@0.9.8 bundle openapi.json \
          --title "shell_service API docs" \
          --cdn
	rm -f openapi.{yml,json}
	mkdir -p doc/_build/html
	mv redoc-static.html doc/openapi.html

