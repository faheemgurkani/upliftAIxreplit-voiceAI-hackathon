# Security

## Reporting a vulnerability

If you find a security issue in this hackathon project, do **not** open a public issue.

Contact a project lead / teammate privately with:

- What the issue is
- Steps to reproduce
- Potential impact

## Secrets

- Never commit `.env`, API keys, tokens, or credentials.
- Use `.env.example` only for non-secret placeholders.
- Rotate any key that may have been exposed.

## Voice / audio data

Treat user audio and transcripts as sensitive. Prefer ephemeral processing for demos unless storage is explicitly required and disclosed.
