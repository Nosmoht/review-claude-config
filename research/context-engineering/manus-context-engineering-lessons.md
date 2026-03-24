# Context Engineering for AI Agents: Lessons from Building Manus

**Source:** [Manus Blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
**Fetched:** 2026-03-24

## Approach

Manus chose to "bet on context engineering" rather than training end-to-end models. Their approach leverages in-context learning abilities of frontier LLMs, allowing them to "ship improvements in hours instead of weeks." They describe their iterative process as "Stochastic Graduate Descent" — manual architecture searching, prompt refinement, and empirical testing. They rebuilt their agent framework four times after discovering better ways to structure context.

## Key Techniques That Worked

### 1. Design Around KV-Cache Hit Rate
They identify KV-cache efficiency as "the single most important metric for a production-stage AI agent." With Claude Sonnet, cached tokens cost $0.30/MTok versus $3/MTok uncached — a 10x difference.

Practices:
- Keep prompt prefixes stable (single-token differences invalidate cache)
- Make context append-only with deterministic serialization
- Explicitly mark cache breakpoints when needed
- Use session IDs to route requests consistently across distributed workers

### 2. Mask, Don't Remove Tools
Rather than dynamically removing tools from the action space, they "mask the token logits during decoding to prevent selection of certain actions." This avoids breaking KV-cache and prevents schema violations when previous observations reference unavailable tools.

### 3. File System as Extended Context
They treat "the file system as the ultimate context" — unlimited, persistent, and directly operable. They compress observations reversibly (preserving URLs when dropping page content) to shrink token usage without permanent information loss.

### 4. Recitation for Attention Management
Manus creates and updates a `todo.md` file throughout task execution. By "reciting objectives into the end of the context," they push goals into the model's recent attention span, avoiding "lost-in-the-middle" issues.

### 5. Preserve Error Evidence
They deliberately "leave the wrong turns in the context." When models see failed actions and resulting stack traces, they "implicitly update internal beliefs," reducing repeated mistakes. Error recovery is framed as "one of the clearest indicators of true agentic behavior."

### 6. Avoid Few-Shot Brittleness
They introduce "structured variation in actions and observations — different serialization templates, alternate phrasing, minor noise in order or formatting" to break repetitive patterns that cause agent drift or hallucination.

## What Didn't Work

- **Dynamic action space loading (RAG-like approach):** Broke KV-cache and confused the model
- **Aggressive context truncation/compression:** Irreversibly loses information the agent might need later
- **Hiding errors or resetting model state:** Removes learning signal
- **Uniform context patterns:** Makes agents brittle and prone to overgeneralization

## Metrics

- **Input-to-output ratio:** Manus averages 100:1 token ratio (heavily prefill-weighted)
- **Tool calls per task:** ~50 tool calls on average
- **Real-world validation:** "Real-world testing across millions of users" (now part of Meta)

Their evidence is primarily empirical rather than benchmark-based; they note that academic work underrepresents error recovery compared to ideal-condition task success.
