# Domain Knowledge Impact on LLM Agent Quality

**Sources:** Multiple academic papers (WebSearch 2026-03-24)

## Key Finding

Domain-specific knowledge significantly improves LLM agent task completion quality. This contradicts the assumption that structural evaluation alone (prompt/context engineering quality) is sufficient — domain knowledge is necessary to assess whether an agent will actually achieve its goal.

## Evidence

### Rule-Based Domain Knowledge Integration
**Source:** [arXiv 2601.15153](https://arxiv.org/html/2601.15153) — "How to Build AI Agents by Augmenting LLMs with Codified Human Expert Domain Knowledge?"

- **LLMs with rules perform 30% better** than LLMs without rules
- Evaluations across five scenarios spanning multiple engineering domains with 12 evaluators demonstrate **206% improvement in output quality**
- Agents achieving **expert-level ratings in all cases** versus baseline's poor performance

### Procedural Knowledge
**Source:** [arXiv 2511.07568](https://arxiv.org/pdf/2511.07568) — "Procedural Knowledge Improves Agentic LLM Workflows"

- Hierarchical Task Network (HTN) decomposition in agentic LLM workflows **significantly increased task success in difficult multi-step tasks**
- This improvement is **effective regardless of the base LLM**

### Domain-Enhanced Framework (GSI Agent)
**Source:** GSI Agent study — domain-enhanced LLM framework

- Combining supervised fine-tuning, retrieval augmentation, and agent-based coordination **substantially improves performance on domain tasks**
- BLEU-4 on the GSI dataset increasing from **0.090 to 0.307** after applying domain enhancement
- Performance on common knowledge datasets remains stable

### Construction Knowledge Enhancement
**Source:** Knowledge-enhanced framework study

- A framework incorporating a Collaborative Expert Module and Knowledge-Injected training strategy **outperforms baseline models by 8.2% in ROUGE-L and 9.0% in semantic similarity**
- Surpasses state-of-the-art models like GPT-4 Turbo and DeepSeek V3

### Prompt Vocabulary Specificity
**Source:** [arXiv 2505.17037](https://arxiv.org/abs/2505.17037) — "Prompt Engineering: How Prompt Vocabulary affects Domain Knowledge"

- Nuanced finding: While generally increasing prompt specificity does not have a significant impact, there appears to be a **specificity range across all models where the LLM performs the best**
- Domain-specific vocabulary matters most in specialized fields (STEM, medicine, law)

## Implications for Skill/Agent Evaluation

1. **Completeness cannot be assessed without domain knowledge.** A Kubernetes troubleshooting skill that's beautifully structured but misses CRD ordering dependencies would score high on structure but fail in practice.

2. **Goal Alignment is the highest-value dimension.** It captures whether the item will actually work in its intended domain, which is where the biggest quality gains exist.

3. **Domain research per item is justified** despite the WebSearch cost/latency, because:
   - Subagent isolation prevents noisy results from polluting other analyses
   - Graceful degradation when WebSearch fails means no hard dependency
   - The alternative (structural-only review) misses the most impactful improvements
