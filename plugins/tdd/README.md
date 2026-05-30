# tdd

Test-driven development with the red-green-refactor loop.

The skill emphasises **vertical slices via tracer bullets** (one test → one minimal
implementation → repeat) over horizontal slicing (all tests first, then all code),
and tests that verify **behavior through public interfaces** rather than implementation
details — so tests survive refactors.

When planning, it consults the project's **domain glossary** so test names and interface
vocabulary match the project's language. This pairs directly with the `harness-init`
plugin, which establishes `docs/glossary.md` as the authoritative glossary.

## Skill

| Skill | Trigger |
|-------|---------|
| `tdd` | Building a feature or fixing a bug test-first, "red-green-refactor", integration tests |

## Reference files

The skill loads these on demand:

- `tests.md` — what good vs. bad tests look like
- `mocking.md` — when (and when not) to mock
- `deep-modules.md` — small interface, deep implementation
- `interface-design.md` — designing interfaces for testability
- `refactoring.md` — refactor candidates to look for once green

## Installation

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install tdd@kinchi22-claude-plugins
```

## Attribution

Mirrored from [mattpocock/skills](https://github.com/mattpocock/skills) (`skills/engineering/tdd`),
licensed under the MIT License. See [LICENSE](LICENSE).
