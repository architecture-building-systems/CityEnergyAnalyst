# Guidelines for LLMs

**Creating new documentation for agents (e.g. AGENTS.md` or `CLAUDE.md`)**:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- **Don't create AGENTS.md in every directory** - Only create when the directory contains complex patterns that aren't obvious from code

**When to create AGENTS.md**:
- **DO create** when the directory has:
  - Complex architectural patterns not obvious from code

- **DON'T create** when:
  - Directory contains simple utility functions
  - Code is self-explanatory with good docstrings
  - It's a small module with straightforward logic
  - Parent directory's AGENTS.md already covers it adequately
  - Would duplicate information already in code/docstrings

**Writing style for AGENTS.md**:
- **Be concise and actionable** - ALWAYS aim for <150 lines when possible
- **Focus on patterns, not details** - What to do, not why it exists
- **Scannable structure** - Use headers, bullets, and short paragraphs

**Updating existing agent documentation**:
- **IMPORTANT**: When making code changes in a directory, ALWAYS update the corresponding `AGENTS.md` file in that directory
- **Create comprehensive user documentation** - When detailed explanations are needed, create proper documentation in `docs/` with sections, examples, and context for human readers. AGENTS.md should remain concise LLM reference only

**Code quality directives**:
- **Extract meaningful patterns, not trivial wrappers** - Only create helper functions when they add real value:
  - **DON'T extract** when:
    - It's just a 1-2 line wrapper around existing functions
    - It's standard library usage (file I/O, simple pandas operations)
    - The abstraction obscures rather than clarifies intent
    - It would be clearer to just write inline
  - **Rule of thumb**: If the helper function is shorter/simpler than its call sites, don't extract it
---
## Project Overview

City Energy Analyst (CEA) - Urban building energy simulation platform for low-carbon city design.

## Environment Setup

**Pixi (Recommended)**:
```bash
pixi install && pixi run setup-dev
pixi run cea dashboard  # Run dashboard
```

**Docker**:
```bash
docker build -t cea .
docker run -p 5050:5050 cea  # Dashboard on port 5050
```
