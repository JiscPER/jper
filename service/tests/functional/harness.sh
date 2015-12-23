#!/bin/sh

# convenience script for executing the test harness.  This specifies some reasonable default values
# but you should take a copy of this script and modify the parameters to your particular test.

python harness.py --timeout 600 \
    --base_url http://localhost:5024/api/v1 \
    --tmpdir harness_tmp \
    --pub_keys pub_keys.txt \
    --repo_keys repo_keys.txt \
    --repo_configs repo_configs.json \
    --validate_threads 1 \
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
    --create_retrieverate 0.05 \
    --create_routable 1.0 \
    --listget_threads 1 \
    --listget_throttle 1 \
    --listget_genericrate 0.05 \
    --listget_maxlookback 7776000 \
    --listget_errorrate 0.1 \
    --listget_getrate 0.05
