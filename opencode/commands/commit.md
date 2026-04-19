# Commit Command

Generate a concise commit message based on current changes and create a git commit.

## Task

1. Run `git status` to see staged and unstaged changes
2. Run `git diff` to see both staged and unstaged changes in detail
3. Analyze the changes and generate a commit message following the conventional commits format
4. Stage relevant files automatically if needed
5. Create the commit with the generated message
6. **CRITICAL: Do NOT include ANY Claude or AI attribution in the commit message**
7. Do NOT push to remote

## Commit Message Format

```
<type>: <short description (under 50 characters)>

- <bullet point 1>
- <bullet point 2>
- <bullet point 3>
- <bullet point 4 (optional)>
- <bullet point 5 (optional)>
```

## Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config, etc.)
- `perf`: Performance improvements
- `style`: Code style changes (formatting, whitespace)

## Guidelines

- Keep header under 50 characters
- Use 3-7 bullet points for the body
- Focus on "why" and "what", not "how"
- Use present tense ("Add feature" not "Added feature")
- Be specific but concise
- Group related changes logically

## ⚠️ CRITICAL: No Attribution

**NEVER include these lines or similar attribution:**
- `🤖 Generated with [Claude Code](https://claude.ai/code)`
- `Co-Authored-By: Claude <noreply@anthropic.com>`
- Any Claude, AI, or automation attribution
- Any emojis in commit messages

## Example Commit Message

```
feat: Add JWT authentication system

- Implement token generation with 24h expiration
- Add bcrypt password hashing for credentials
- Create login/logout API endpoints
- Add auth middleware for protected routes
- Update user model with password fields
```

## Important Notes

- Stage files intelligently (exclude temp files, build artifacts)
- If no changes are staged, stage relevant modified files
- Warn if about to commit sensitive files (.env, credentials)
- After committing, display the commit SHA and message
- Remind that manual push is required
