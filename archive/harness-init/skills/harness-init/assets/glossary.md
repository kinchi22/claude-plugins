# Domain glossary

**This file is the authoritative source for the project's domain vocabulary.** When a
term here conflicts with code, comments, or a PRD, this file wins — fix the other
place. When you introduce or rename a domain concept, update this glossary in the same
change so the two never drift apart.

Use these terms verbatim in code (types, functions, modules), tests, PRDs, ADRs, and
commit messages. Shared words are how sessions stay aligned across fresh contexts.

## How to use

- **Before naming something**, check whether the concept already has a term here.
- **Before inventing a synonym**, reuse the existing term — one concept, one word.
- **When a term changes meaning**, edit its entry and note what changed.

## Terms

<!-- Seed with the project's core domain concepts. One concept per entry. -->

### Example: Cart

A user's collection of items pending checkout. Belongs to exactly one user. Distinct
from an **Order**, which is a Cart that has been confirmed and paid.

> Replace these examples with real terms. Keep definitions short, precise, and written
> in terms of other glossary entries where possible.
