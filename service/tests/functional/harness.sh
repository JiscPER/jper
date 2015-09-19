#!/bin/sh
python harness.py --timeout 60 --base_url http://localhost:5024/api/v1 --tmpdir harness_tmp --pub_keys pub_keys.txt \
    --validate_threads 0 \
    --validate_throttle 1 \
    --validate_mdrate 0.1 \
    --validate_mderrors 0.8 \
    --validate_cterrors 0.8 \
    --validate_maxfilesize 1 \
    --create_threads 1 \
    --create_throttle 1 \
    --create_mdrate 0.1 \
    --create_mderrors 0.05 \
    --create_cterrors 0.05 \
    --create_maxfilesize 1 \
    --create_retrieverate 1