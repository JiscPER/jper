#!/bin/sh
python harness.py --timeout 60 --base_url http://localhost:5024/api/v1 --tmpdir harness_tmp --pub_keys pub_keys.txt \
    --validate_threads 3 \
    --validate_throttle 1 \
    --validate_mdrate 0.1 \
    --validate_mderrors 0.8 \
    --validate_cterrors 0.8 \
    --validate_maxfilesize 1