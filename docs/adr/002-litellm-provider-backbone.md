# ADR-002: LiteLLM as Provider Backbone

## Status
Accepted

## Context
Need to support multiple LLM providers (Claude, GPT, Gemini, Ollama, llama.cpp, etc.)
with a unified interface. Options:
1. Build custom provider abstraction from scratch
2. Use LiteLLM as backbone
3. Use LangChain's LLM abstraction

## Decision
Use LiteLLM as the backbone for provider abstraction.

## Rationale
- LiteLLM already supports 100+ providers
- Built-in retry, fallback, cost tracking
- Active maintenance and community
- Reduces development time from months to days
- Our Provider layer adds value with health checks, capability negotiation, and custom extensions

## Consequences
- Dependency on LiteLLM's API stability
- Less control over provider-specific features
- Need thin wrapper layer for platform-specific concerns

## Mitigation
- Keep our Provider interface stable and independent
- Wrapper layer isolates LiteLLM changes
- Can swap LiteLLM for custom implementation if needed
