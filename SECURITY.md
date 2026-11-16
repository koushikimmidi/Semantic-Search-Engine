# Security policy

## Supported versions

Security fixes are made on the latest release on the `main` branch.

| Version | Supported |
| --- | --- |
| 2.x | ✅ |
| < 2.0 | ❌ |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report it privately through GitHub:
**Security → Report a vulnerability** on this repository
(<https://github.com/koushikimmidi/Semantic-Search-Engine/security/advisories/new>).

Include what you found, how to reproduce it, and the impact you expect. You will get an
acknowledgement within a few days, and a fix or mitigation plan once the issue is confirmed.

## Deployment checklist

- Set a long random `ADMIN_API_KEY` and keep `.env` private (it is git-ignored).
- Serve the app over HTTPS when it is reachable from the internet.
- Keep automatic email replies off until you have reviewed answer quality.
- Restrict who can reach the API (firewall / reverse proxy) if it handles sensitive data.
- Keep dependencies up to date (Dependabot is configured for this repository).
