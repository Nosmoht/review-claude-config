---
name: eval-test-reliability-agent
description: >
  Processes data by spawning subagents for each data source, fetches external
  content, and persists results. Use for data processing pipelines.
allowed-tools: Agent, WebFetch, Write, Read
---

# Eval Test Reliability Agent

## Workflow

### Step 1: Spawn source agents

Launch three subagents via the Agent tool, one per data source:
- Agent A: fetch data from https://api.source-a.example.com/data
- Agent B: fetch data from https://api.source-b.example.com/data
- Agent C: fetch data from https://api.source-c.example.com/data

Collect all three results.

### Step 2: Fetch supplementary content

Use WebFetch to retrieve https://reference.example.com/catalog for metadata enrichment.

### Step 3: Merge results

Combine the three agent outputs with the WebFetch content into a single merged dataset.

### Step 4: Persist

Write the merged dataset to output/results.json using Write.

### Step 5: Report

Output a summary of the processed records.
