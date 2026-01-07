---
layout: single
title: "Contribution process documentation"
permalink: /contribution-process/

classes: wide
toc: false
toc_label: "Describe the contribution process"
toc_icon: "hands-helping"
---

## Overview

This document describes the end-to-end process for managing anonymous contributions to the Audierne-Esquibien 2026 participatory campaign program. The process ensures anonymity, transparency, and democratic deliberation before integrating citizen proposals into the electoral platform.

## Process Flow

```
Anonymous Form → Email → GitHub Issue → Discussion → Program Integration
```

## Detailed Stages

### Stage 1: Anonymous Submission

**Timeline:** Continuous
**Actors:** Citizens

Citizens submit their ideas through thematic online forms (Framaforms):

- Economy
- Housing & Urban Planning
- Culture & Heritage
- Associations & Local Life
- Education & Youth
- Environment
- Food, Wellness & Healthcare

**Key characteristics:**

- **Complete anonymity**: No personal data collected
- **Thematic organization**: Submissions are pre-categorized
- **Open access**: Available to all residents and interested parties

### Stage 2: Automated Aggregation

**Timeline:** Daily at 8:00 UTC (9:00 France time)
**Actors:** GitHub Actions workflow

The `poll_email.py` script automatically:

1. Connects to the campaign email inbox
2. Retrieves Framaforms submissions from the previous day
3. Counts contributions by category
4. Creates a daily report as a GitHub Issue

**Anonymity preservation:**

- Only aggregated statistics are published
- Individual submission content is NOT automatically published
- Labels: `rapport`, `framaforms`, `automatisé`

**Manual reruns:**

- Script: `rerun_poll_email.py <DD/MM/YYYY>`
- Allows processing specific dates
- Logs saved in `/logs/` directory
- Issues tagged with additional `rerun` label

### Stage 3: Compliance Review

**Timeline:** Within 7 days of submission
**Actors:** Campaign team

Team members review each contribution against the [contribution charter](/contribuer.md#charte-de-contribution):

**✅ Accepted contributions:**

- Concrete, reasoned proposals
- Constructive criticism
- Questions and clarification requests
- Experience and expertise sharing
- Improvement suggestions

**❌ Rejected contributions:**

- Personal attacks or discriminatory remarks
- Spam or advertising
- Proposals unrelated to Audierne-Esquibien
- Misinformation

**Action:** Issue labeled `conforme charte` (compliant with charter) or closed with explanation.

### Stage 4: Contextualization

**Timeline:** Variable (days to weeks)
**Actors:** Campaign team + GitHub community

For compliant contributions, the team:

1. Creates a GitHub Issue with:
   - Thematic label (economie, logement, culture, etc.)
   - `conforme charte` label
   - Contextual information and initial analysis
2. Invites public commentary and additional context
3. Links related issues and proposals
4. Facilitates constructive debate

**Status labels:**

- `en cours` (in progress)
- `documentation` (needs more info)
- `discussion` (active debate)

**Duration:** Issues remain open as long as necessary for adequate contextualization.

### Stage 5: Discussion Migration

**Timeline:** When context is sufficient
**Actors:** Campaign team

Once an issue has been adequately contextualized:

1. Content is migrated to [GitHub Discussions](https://github.com/audierne2026/participons/discussions)
2. Original issue is closed with link to discussion thread
3. Broader community engagement is encouraged
4. Long-form debate and deliberation occurs

**Goal:** Allow mature, informed public discourse on each proposal.

### Stage 6: Program Integration

**Timeline:** Early February 2026
**Actors:** Campaign team + community

After sufficient deliberation time (TBD):

1. **Consolidation process** synthesizes discussion outcomes
2. Accepted proposals are drafted into program text
3. Draft is published for final community review
4. Finalized proposals are integrated into the official platform
5. All decisions are documented with full traceability

**Transparency:** Every step from submission to integration is publicly documented on GitHub.

## Rationale

This process addresses several key challenges:

### Anonymity vs. Accountability

- Forms allow truly anonymous participation
- Team-curated issues prevent abuse while preserving anonymity
- Public discussion ensures transparency without exposing contributors

### Signal vs. Noise

- Automated aggregation shows participation trends
- Manual review filters non-constructive contributions
- Contextualization adds depth and nuance

### Deliberation vs. Efficiency

- Issues allow quick initial review and contextualization
- Discussions enable deeper, longer-term deliberation
- Clear timeline (early February) ensures process completion before campaign

### Transparency vs. Workload

- Automation handles routine aggregation
- Team focuses on high-value curation and contextualization
- GitHub provides free, auditable infrastructure

## Metrics and Reporting

**Daily reports track:**

- Number of submissions per category
- Participation trends over time

**Process metrics:**

- Time from submission to compliance review
- Time from issue creation to discussion migration
- Number of community engagements per proposal
- Integration rate (accepted/total submissions)

## Tools and Infrastructure

**Submission:**

- Framaforms (privacy-respecting, no tracking)

**Automation:**

- GitHub Actions (daily scheduled workflow)
- Python scripts (`poll_email.py`, `rerun_poll_email.py`)
- IMAP email integration

**Collaboration:**

- GitHub Issues (contextualization phase)
- GitHub Discussions (deliberation phase)
- Git/GitHub (program version control)

**Documentation:**

- Markdown files
- Jekyll static site (https://audierne2026.github.io/participons/)

## Open Questions

1. **Discussion maturity criteria:** How long should discussions remain open before consolidation?
2. **Voting mechanisms:** Should community votes influence integration decisions? If so, how?
3. **Feedback loops:** How to inform anonymous contributors about the fate of their proposals?
4. **Scalability:** What if submissions exceed team capacity to contextualize?

## Revision History

- **2026-01-07:** Initial documentation
- **Future:** To be updated as process evolves through campaign

---

**License:** This process is part of the Audierne-Esquibien 2026 open campaign.
**Repository:** https://github.com/audierne2026/participons
**Contact:** Via GitHub Issues or Discussions
