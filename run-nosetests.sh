#!/bin/sh
#set -x
set -e

geoss_search init tests/test_data/geoss_open_resp.json --with-schema tests/test_data/schema.yml --force

exec nosetests $@
