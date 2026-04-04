---
last_refreshed: 2026-04-03
---

# Writing Effective Tools for AI Agents

## Provenance Metadata

- Strongest source tier: Tier 1
- Source basis: Single source - Anthropic Engineering Blog, "Writing tools for agents"
- Last reviewed: 2026-04-03

**Source:** [Anthropic Engineering Blog](https://www.anthropic.com/engineering/writing-tools-for-agents)
**Fetched:** 2026-03-24

## Key Insight

Tool descriptions are "one of the most effective methods for improving tools." The guidance recommends treating descriptions as if explaining to a new team member — making implicit context explicit.

"Small refinements to tool descriptions can yield dramatic improvements," citing Claude Sonnet's state-of-the-art performance on SWE-bench after precise description adjustments.

## Best Practices

### Description Quality
- Use unambiguous parameter names (e.g., `user_id` instead of `user`)
- Clearly describe expected inputs and outputs with strict data models
- Avoid vague terminology without definitions
- Test description effectiveness through evaluation metrics

### Context Efficiency
Agents have limited context windows unlike computers with abundant memory. Rather than returning all data, tools should implement "pagination, range selection, filtering, and/or truncation." Returning only high-signal information prevents wasting an agent's limited processing capacity on irrelevant data.

### Response Format
Tool response structure — XML, JSON, or Markdown — affects performance differently depending on the task, as "LLMs are trained on next-token prediction" and perform better with familiar formats.

### Meaningful Identifiers
Replacing cryptic UUIDs with semantic language "significantly improves Claude's precision in retrieval tasks by reducing hallucinations."

## Anti-Patterns

1. **Over-Wrapping APIs:** "Tools that merely wrap existing software functionality or API endpoints" without considering agent affordances create ineffective designs.

2. **Excessive Tool Count:** "More tools don't always lead to better outcomes." Too many overlapping tools distract agents from efficient strategies.

3. **Unhelpful Error Messages:** Error responses should provide "specific and actionable improvements, rather than opaque error codes or tracebacks."

4. **Vague Tool Purposes:** When multiple tools overlap in function, agents become confused about selection.

5. **Context-Wasteful Designs:** Tools returning entire datasets force agents to inefficiently search token-by-token through irrelevant information.

## Tool Set Scoping

### Selective Implementation
Build "a few thoughtful tools targeting specific high-impact workflows" rather than attempting comprehensive API coverage. Match tools to actual evaluation tasks and user needs.

### Consolidation Over Proliferation
Tools can "handle potentially multiple discrete operations under the hood." Rather than separate `list_users`, `list_events`, and `create_event` tools, implement a single `schedule_event` tool that handles availability checking and creation.

### Namespacing
Group related tools under common prefixes (e.g., `asana_projects_search`, `asana_users_search`) to help agents select appropriate tools. "Selecting between prefix- and suffix-based namespacing" produces measurable evaluation differences.

### Clear Distinct Purpose
Each tool should enable agents to "subdivide and solve tasks in much the same way that a human would," reducing intermediate context consumption while maintaining clear functional boundaries.

**Overarching principle:** Design tools for agent cognition, not API comprehensiveness.
