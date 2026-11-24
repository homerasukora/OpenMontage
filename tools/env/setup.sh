#!/bin/bash
# Cloud environment setup script (paste into: environment menu -> Edit -> Setup script).
# Installs the Higgsfield CLI and its Claude Code skills. Sign-in is per session: `higgsfield auth login`.
set -euo pipefail

# Higgsfield CLI (`higgsfield` / `hf`)
npm install -g @higgsfield/cli

# Higgsfield companion skills for Claude Code (installed globally into ~/.claude/skills)
npx -y skills add higgsfield-ai/skills -g -a claude-code -y

higgsfield version
# free-video: CLI over Open Generative AI / MuAPI (needs MUAPI_API_KEY)
ln -sf /home/user/OpenMontage/tools/free_video/free_video.py /usr/local/bin/free-video || true
