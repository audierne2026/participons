# env-templates — audierne2026

Templates for the sovereign `.env` files, split by **concern** (blast radius), not by
environment. App class: **free electron** — a static Jekyll site (`audierne2026.fr`) with a
Python content pipeline. It binds **no slot, no port, no Redis**. Only the concerns the
pipeline genuinely consumes are templated here.

## The Ordnung

**dotenv-radius-only policy:** every file follows `.env.<concern>`. No bare `.env`. Local dev
variants follow `.env.<concern>.dev` (loaded after the base — dev wins).

| File | Template | Concern | Rotation trigger |
|------|----------|---------|------------------|
| `.env.config` | `env.config.example` | Identifiers only (`GITHUB_REPOSITORY`, `EMAIL_USER`) | never |
| `.env.claude` | `env.claude.example` | LLM keys (`ANTHROPIC_API_KEY`, `MISTRAL_OCR_API_KEY`) | IDE/context breach, seasonal |
| `.env.infra` | `env.infra.example` | Mail password, the participonsmobile connector | service breach, seasonal |
| `.env.platforms` | `env.platforms.example` | GitHub: the ocapistaine bot (`OCAPISTAINE_GITHUB_TOKEN`), the project PAT (`AUDIERNE_GITHUB_PAT_TOKEN`) | expiry, GitHub/bot compromise |

> **Omitted by design (free electron).** `.env.webhooks` · `.env.apps` · `.env.agents` are N/A —
> no Discord channel, no app runtime, no per-agent forge token consumed by this repo. Add a
> template the day a concern becomes real, never before.

> **CI reads none of these files.** GitHub Actions reads the repository's own secrets
> (`OCAPISTAINE_GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `EMAIL_USER`,
> `EMAIL_PASS`) and the built-in `GITHUB_TOKEN`. A rotation is done in both places.

## Setup

```bash
cp env-templates/env.config.example    .env.config
cp env-templates/env.claude.example    .env.claude
cp env-templates/env.infra.example     .env.infra
cp env-templates/env.platforms.example .env.platforms
# fill each <forseti - ok> with the real value, then run a script through the loader:
bash scripts/dev-env.sh python3 scripts/export_contributions_to_md.py
```

`scripts/dev-env.sh` loads the four layers in order and stops on a missing one.
