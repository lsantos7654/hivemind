# Generate PR Description

Generate a concise pull request description based on changes between the current branch and main branch.

## Task

1. Run `git diff main` to analyze all changes since branching from main
2. Read the current `PR_DESCRIPTION.md` file in the project root if it exists
3. Generate or update a concise PR description that includes:
   - **Summary**: 2-3 sentences explaining the overall purpose of the changes
   - **Key Changes**: 3-7 bullet points highlighting the most important modifications
   - **Testing**: Brief notes on how changes were tested (if applicable from code)
   - **Notes**: Any important caveats, dependencies, or follow-up items

4. Write the description to `PR_DESCRIPTION.md` in the project root directory

## Style Guidelines

- Keep it concise and focused on "why" not just "what"
- Use present tense ("Add feature" not "Added feature")
- Prioritize user-facing changes and architectural decisions
- Group related changes together
- Omit trivial changes (formatting, typos) unless significant

## Example Format

```markdown
## Summary

Add user authentication system with JWT token support and password hashing for secure login/logout functionality.

## Key Changes

- Implement JWT token generation and validation with 24-hour expiration
- Add bcrypt password hashing for secure credential storage
- Create `/auth/login` and `/auth/logout` API endpoints
- Add authentication middleware for protecting routes
- Update user database model with password and token fields

## Testing

- Unit tests for token generation and validation
- Integration tests for login/logout flows
- Manual testing with Postman

## Notes

- Requires environment variable `JWT_SECRET` to be set
- Password reset functionality will be added in follow-up PR
```

IMPORTANT: Actually read the git diff and analyze the code changes. Don't just generate a template.
