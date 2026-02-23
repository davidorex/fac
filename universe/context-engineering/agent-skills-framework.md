# Agent Skills for Context Engineering

Source: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering

## What This Framework Is

A comprehensive collection of reusable skills designed to help developers build production-grade AI agent systems. Rather than focusing on prompt engineering alone, this framework emphasizes **context engineering** — the strategic curation of all information entering an LLM's attention window.

## Core Concept

"Context engineering is the discipline of managing the language model's context window" by optimizing system prompts, tool definitions, retrieved documents, message history, and outputs. The framework acknowledges that models experience predictable performance degradation patterns like the "lost-in-the-middle" phenomenon as context length increases.

## Skill Categories

The repository organizes content into five main categories:

**Foundational**: context-fundamentals, context-degradation, and context-compression
**Architectural**: multi-agent-patterns, memory-systems, tool-design, filesystem-context, and hosted-agents
**Operational**: context-optimization, evaluation, and advanced-evaluation
**Development**: project-development methodology
**Cognitive**: bdi-mental-states (formal reasoning)

## Key Design Principles

1. **Progressive Disclosure** — Skills load only their descriptions initially; full content activates when relevant
2. **Platform Agnostic** — Principles transfer across Claude Code, Cursor, and other agent frameworks
3. **Practical Examples** — Python pseudocode demonstrates concepts without framework dependencies

## Why This Matters for the Factory

This framework provides the theoretical foundation for:
- The context budget monitoring system (GREEN/YELLOW/ORANGE/RED/DARK RED thresholds)
- Progressive skill disclosure (names + descriptions first, full content on request)
- The compaction trigger at 90%+ context usage
- Why agents should write to disk before context fills up
- The U-shaped attention curve that makes middle-of-context content less reliable

The individual skill files in this directory (context-fundamentals.md, context-degradation.md, etc.) contain the detailed technical content from the framework.

License: MIT
