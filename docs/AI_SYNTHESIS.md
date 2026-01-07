# AI-Powered Contribution Synthesis

## Overview

This document describes the AI-powered synthesis system that generates weekly summaries of citizen contributions for the Audierne2026 participatory campaign.

The system uses **Claude API** (Anthropic) to intelligently analyze and summarize contributions, producing a one-page French report organized by program category.

---

## Architecture

```
GitHub Issues (Contributions)
         ↓
    GitHub API
         ↓
  ai_synthesis.py
         ↓
    Claude API
         ↓
  One-page French Summary
         ↓
  GitHub Issue (Report)
```

## Components

### 1. Data Collection (`scripts/ai_synthesis.py`)

The script:
1. Connects to GitHub API
2. Fetches issues labeled `conforme charte` (validated contributions)
3. Retrieves comments (team contextualizations)
4. Groups contributions by program category
5. Prepares data for AI summarization

### 2. AI Summarization (Claude API)

Claude receives:
- All contributions organized by category
- Instructions to generate a concise French summary
- Guidelines for structure and tone

Claude produces:
- One-page summary (max ~400 words)
- Key points per category
- Actionable recommendations
- Issue references (#XX)

### 3. Distribution (GitHub Actions)

The workflow:
- Runs manually or on schedule
- Creates a GitHub Issue with the synthesis
- Saves the report as an artifact

---

## Setup Instructions

### Prerequisites

- GitHub repository with contribution issues
- Anthropic API account
- GitHub Actions enabled

### Step 1: Obtain Claude API Key

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Create an account or sign in
3. Navigate to **API Keys**
4. Create a new key
5. Copy the key (format: `sk-ant-api03-...`)

### Step 2: Configure GitHub Secrets

Go to your repository settings:
`Settings → Secrets and variables → Actions → New repository secret`

Add the following secret:

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | Your Claude API key |

*Note: `GITHUB_TOKEN` is automatically provided by GitHub Actions.*

### Step 3: Deploy the Workflow

The workflow file is located at:
`.github/workflows/synthese_ia.yml`

Push changes to your repository:
```bash
git add scripts/ai_synthesis.py .github/workflows/synthese_ia.yml
git commit -m "Add AI synthesis workflow"
git push
```

---

## Usage

### Manual Trigger (Recommended)

1. Go to **Actions** tab in your repository
2. Select **"Synthèse IA des contributions"**
3. Click **"Run workflow"**
4. Configure options:
   - **Période en jours**: Number of days to analyze (default: 7)
   - **Créer une issue**: Whether to create a GitHub issue with the report
5. Click **"Run workflow"**

### Scheduled Run (Optional)

To enable weekly automatic runs, uncomment these lines in the workflow:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Every Monday at 8am UTC
```

### Local Execution

For local testing:

1. Create a `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key
GITHUB_TOKEN=ghp_your-github-token
GITHUB_REPO=audierne2026/participons
```

2. Install dependencies:
```bash
pip install requests python-dotenv
```

3. Run the script:
```bash
python scripts/ai_synthesis.py --days 7 --output synthese.md
```

---

## Output Format

### Sample Synthesis

```markdown
# Synthèse des contributions citoyennes

**Période :** 7 derniers jours

## Logement & Urbanisme
**3 contributions**

Les citoyens soulèvent principalement la question de l'ancienne
école maritime (#38) avec une proposition de réhabilitation en
lieu culturel. Cette idée rejoint les objectifs du programme sur
la préservation du patrimoine.

**Points clés :**
- Réhabilitation du bâtiment abandonné rue Amiral Guepratte
- Création d'un espace polyvalent (culturel/apprentissage)
- Besoin d'étude de faisabilité

## Environnement
**2 contributions**

Préoccupation sur les dunes de Trez Goarem (#15, #14) : conflit
entre promenades canines et protection des oiseaux nicheurs.

**Proposition :** Identifier un terrain alternatif moins sensible.

## Pistes d'action

1. Prioriser l'étude de faisabilité pour l'école maritime
2. Organiser une concertation sur Trez Goarem avec associations
3. Enrichir la section Environnement du programme
```

---

## Configuration Options

### Script Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--days`, `-d` | 7 | Time window in days |
| `--output`, `-o` | `synthese_ia.md` | Output file path |
| `--no-ai` | False | Disable AI, use basic extraction |

### Workflow Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `days` | 7 | Period to analyze |
| `create_issue` | true | Create GitHub issue with report |

---

## AI Prompt Design

The prompt instructs Claude to:

1. **Stay factual**: Only use provided contribution data
2. **Be concise**: Maximum 400 words total
3. **Structure clearly**: Use markdown headings per category
4. **Reference issues**: Cite #XX numbers when relevant
5. **Provide actions**: Include 3 concrete recommendations
6. **Use French**: All output in French

### Prompt Template

```
Tu es un assistant pour la campagne municipale Audierne2026.
Tu dois générer une synthèse en français des contributions
citoyennes reçues ces {days} derniers jours.

[Contribution data in JSON format]

Génère une synthèse d'UNE PAGE MAXIMUM en français avec :
1. Un titre "Synthèse des contributions citoyennes"
2. La période couverte
3. Pour CHAQUE catégorie : nombre, points clés, enrichissement programme
4. Une section "Pistes d'action" avec 3 recommandations

IMPORTANT : Reste factuel, cite les numéros d'issues, sois concis.
```

---

## Cost Estimation

Using Claude Sonnet model:

| Metric | Cost |
|--------|------|
| Input tokens | ~$3 / 1M tokens |
| Output tokens | ~$15 / 1M tokens |
| **Per synthesis** | **~$0.01-0.05** |
| **Monthly (4 runs)** | **~$0.04-0.20** |

Very affordable for regular use.

---

## Fallback Mode

If `ANTHROPIC_API_KEY` is not set, the script automatically falls back to basic extraction mode:

- Lists contributions by category
- Shows issue titles and links
- No AI-powered summarization

This ensures the workflow doesn't fail if the API key is missing.

---

## Integration with Contribution Process

This synthesis fits into the broader contribution process:

```
1. Anonymous submission (Framaforms)
        ↓
2. Daily aggregation (poll_email.py)
        ↓
3. Compliance review (Team)
        ↓
4. Contextualization (GitHub Issues)
        ↓
5. AI Synthesis (ai_synthesis.py) ← THIS TOOL
        ↓
6. Discussion migration
        ↓
7. Program integration (February 2026)
```

The AI synthesis helps the team:
- Get a quick overview of recent contributions
- Identify patterns and common themes
- Prioritize which issues need attention
- Track progress toward program integration

---

## Troubleshooting

### Error: 403 from GitHub API

**Cause:** Rate limiting (no token) or insufficient permissions.

**Solution:**
- Ensure `GITHUB_TOKEN` is set
- In Actions, permissions should include `issues: read`

### Error: 401 from Claude API

**Cause:** Invalid or expired API key.

**Solution:**
- Verify `ANTHROPIC_API_KEY` in secrets
- Generate a new key if needed

### Empty synthesis

**Cause:** No contributions matching criteria in the time window.

**Solution:**
- Increase `--days` parameter
- Verify issues have `conforme charte` label

### Synthesis too long

**Cause:** Many contributions in the period.

**Solution:**
- The AI is instructed to stay under 400 words
- Adjust the prompt in the script if needed

---

## Future Enhancements

Planned improvements:

1. **N8N Integration**: Replace script with N8N workflow for more flexibility
2. **TRIZ Analysis**: Include contradiction detection in synthesis
3. **Multi-language**: Support Breton language summaries
4. **Trend Analysis**: Compare with previous periods
5. **Slack/Email Notifications**: Send synthesis to team channels

---

## Related Documentation

- [Contribution Process](./contribution_process.md) - Full process documentation
- [TRIZ Methodology](./TRIZ_METHODOLOGY.md) - Contradiction analysis framework
- [Transparency Charter](./TRANSPARENCY.md) - Data handling principles

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-07 | 1.0 | Initial implementation |

---

## Support

For issues with the AI synthesis:

1. Check the workflow logs in GitHub Actions
2. Open an issue with label `aide`
3. Contact the technical team

---

*This tool is part of the Audierne2026 open participatory campaign.*
*Repository: https://github.com/audierne2026/participons*
