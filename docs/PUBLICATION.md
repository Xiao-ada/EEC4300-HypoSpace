# Publication and reproducibility

Project repository: https://github.com/Xiao-ada/EEC4300-HypoSpace. The course final deliverable is a public repository plus a ten-minute group video with every member presenting. Current publication state is recorded in results/STATUS.json.

Source, measured aggregate results, compressed raw evidence and three reviewed LoRA-only adapters are included. Original base weights, environments, caches, raw private runs, institutional documents and credentials are excluded. MIT covers original source; adapter/base-model attribution and Apache terms are under artifacts/adapters and NOTICE.md.

Before release run scripts/audit_upload.py and scripts/verify_results.py, inspect the figures and links, then commit and push the reviewed tree. Public evidence uses only benchmark observations and model outputs. The optional CI definition is docs/ci_example.yml. No new repository-access scopes are required for the supplied local validation commands.

The team's actual video recording and speaker contributions cannot be replaced by generated notes. Use docs/VIDEO_GUIDE_ZH.md for structure and scripts/show_demo.py for a fixed saved-evidence demonstration.
