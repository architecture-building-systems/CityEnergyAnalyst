# Guidelines for LLMs

**Creating new documentation**:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- This maintains consistency with the existing documentation structure where topic-specific instructions live in `AGENTS.md` files and are symlinked for compatibility

**Updating existing documentation**:
- **Always** update the relevant `AGENTS.md` file when you make changes to code in that directory
- Keep documentation synchronized with code changes to help other LLMs understand the current state
- Focus on architectural patterns, state management, data flow, and key concepts that aren't obvious from code alone
