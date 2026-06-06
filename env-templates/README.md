# env-templates — audierne2026

Templates for the sovereign `.env` files, split by **concern** (blast radius), not by
environment. App class: **free electron** — a static Jekyll site (`audierne2026.fr`) with a
Python content pipeline. It binds **no slot, no port, no Redis**. Only the **one concern that
genuinely applies** is templated here.

## The Ordnung

**dotenv-radius-only policy:** every file follows `.env.<concern>`. No bare `.env`. Local dev
variants follow `.env.<concern>.dev` (loaded with `override=True` — dev wins).

| File | Template | Concern | Rotation trigger |
|------|----------|---------|------------------|
| `.env.claude` | `env.claude.example` | Pipeline + platform tokens (`GITHUB_API`, `OCAP_LOCKI_TOKEN`) | GitHub / bot compromise |

> **Omitted by design (free electron).** `.env.config` · `.env.infra` · `.env.platforms` ·
> `.env.webhooks` · `.env.apps` · `.env.agents` are N/A — no app runtime, no observability
> stack, no Discord channel, no per-agent forge token consumed by this repo. Add a template the
> day a concern becomes real, never before.

> **CONFIG vs SECRET (Forseti0).** Secrets carry a suffix (`_PASSWORD`, `_KEY`, `_TOKEN`,
> `_SECRET`) and live only in their rotation-matched radius. Lifecycle wins: a key belongs in
> the file whose blast radius matches its rotation trigger. The two tokens here are PLATFORM-class
> (canonical home `.env.platforms`); they sit in `.env.claude` for convenience until the next
> rotation window — see the note in `env.claude.example`.

## Setup

```bash
cp env-templates/env.claude.example .env.claude
# fill each <forseti - ok> with the real value, then:
set -a && source .env.claude && set +a
```

## Migration note

The legacy root `.env.example` is superseded by this directory (realm canon: templates ship as
`env-templates/env.<concern>.example`, never a root-scattered bare `.env.example`). Remove the
old root template once this is in place.
