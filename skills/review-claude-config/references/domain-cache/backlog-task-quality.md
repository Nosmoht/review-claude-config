---
domain: backlog-task-quality
last_refreshed: 2026-04-03
queries:
  - "acceptance criteria quality standards agile backlog task completeness best practices"
  - "acceptance criteria verifiable testable INVEST criteria user story quality 2024"
sources:
  - url: https://resources.scrumalliance.org/Article/need-know-acceptance-criteria
    title: "Acceptance Criteria: Everything You Need to Know Plus Examples"
    tier: 1
  - url: https://www.altexsoft.com/blog/acceptance-criteria-purposes-formats-and-best-practices/
    title: "Acceptance Criteria: Purposes, Types, Examples and Best Practices"
    tier: 2
  - url: https://www.atlassian.com/work-management/project-management/acceptance-criteria
    title: "What is Acceptance Criteria? Definition, Examples, & Tips"
    tier: 2
  - url: https://www.testrail.com/blog/acceptance-criteria-agile/
    title: "Acceptance Criteria in Agile Testing"
    tier: 2
  - url: https://agileforall.com/new-to-agile-invest-in-good-user-stories/
    title: "New to Agile? INVEST in Good User Stories"
    tier: 2
---

# Backlog Task Quality — Domain Best Practices

**Definition and purpose**
- Acceptance criteria (AC) are pass/fail conditions a backlog item must satisfy to be considered complete (Scrum Alliance, Tier 1).
- AC serve developers (requirement clarity), QA (test generation), and product owners (scope control) — they are collaborative artifacts, not unilateral outputs.

**Quality properties (industry consensus)**
- **Specific:** Names a concrete artifact, state, or behavior — not a quality attribute.
- **Observable:** A third party can determine pass/fail without subjective judgment.
- **Scoped:** Does not exceed or understate the task boundary.
- **Testable (INVEST "T"):** Clear enough that a tester can write a test case directly from the criterion (AgileForAll, Tier 2).
- **Non-compound:** Each criterion covers one condition — "and" joins are a quality defect.

**Common failure modes**
- Vague language ("appropriate," "adequate," "properly") — untestable, leads to rework (AltexSoft, Tier 2).
- Scope inflation: AC that exceed the user story scope drive unplanned work.
- Assumption smuggling: AC that presume upstream approvals not yet granted.
- Compound criteria: multiple conditions in one statement prevent clean pass/fail assessment.

**Format best practices**
- Given-When-Then (Gherkin) for behavior-driven contexts; numbered declarative list for simpler tasks.
- Minimum 2 criteria per task is a recognized floor; criteria should be exhaustive for the stated scope.
- Define AC before development begins; ideally during refinement 2–3 sprints ahead (Atlassian, Tier 2).

**Impact**
- Vague or missing AC are a leading cause of end-of-sprint scope disputes (TestRail, Tier 2).
- Well-written AC reduce development cycles by reducing ambiguity and rework (Atlassian, Tier 2 — treat metric as indicative; no primary source cited for the specific figure).
