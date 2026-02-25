# multi-cli-runtime

## What I'm Seeing
The factory runtime currently only invokes agents via Claude Code (`claude` CLI). The kimi-cli backend has been built and verified (`runtime/factory_runtime/backends/kimi_cli.py`), but the runtime doesn't yet let the user choose which CLI to use per-agent or globally. Token costs vary significantly between providers, and different parts of the pipeline have different capability requirements — some agents need Opus-class reasoning while others could run on cheaper models from other providers.

## What I Want to See
A user can configure the factory to run agents using either `claude` (Claude Code) or `kimi` (kimi-cli) without losing any functionality. The choice is per-agent in `agents.yaml` (e.g., `backend: kimi` or `backend: claude`), with a sensible default. All existing features — WhatsApp notifications, observation extraction, decision monitoring, next-step hints, run logging — work identically regardless of backend. This sets the groundwork for mixing providers across the pipeline based on cost and capability needs.
