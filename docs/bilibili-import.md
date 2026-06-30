# Bilibili import decision

Reviewed: 2026-06-30

The official open-platform overview documents account authorization, public user information, content management, and authorized data capabilities. The public documentation reviewed for Phase 6 did not identify a viewing-history permission or endpoint. This is a documentation-based inference, not a claim that Bilibili can never grant such access.

Sources:

- [Bilibili Open Platform documentation](https://openhome.bilibili.com/doc)
- [Bilibili Open Platform](https://open.bilibili.com/)
- [Developer service agreement](https://openhome.bilibili.com/agreement/developer-service)

Decision:

1. Do not claim OAuth viewing-history support.
2. Do not scrape private endpoints or request passwords, Cookie, `SESSDATA`, or tokens.
3. Accept only a file that the user intentionally selects.
4. Parse and match the file in browser memory against a downloaded public catalog index.
5. Reject credential-bearing columns and require confirmation for every candidate.
6. Re-evaluate an official integration only after an approved application receives a documented viewing-history scope.
