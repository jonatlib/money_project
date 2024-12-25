#!/bin/bash

docker run -it --rm --user=1000 -v $(pwd):/data/:ro dcycle/ledger:1 -f /data/test $@

