- [ ] change librarian to only be aware of enabled agents
- [ ] need some way to organize or create directories for similar agents in the tui for better organization. Should be able to enable/disable all agents in a directory.
    - [ ] I want to introduce the concept of private agents, essentially this is the same thing as agents except they are not committed to git since they contain confidential info they only live locally.
- [ ] update wording for `Update All` should only update active agents only
- [X] searching is broken, nothing shows up in the search bar, searches do happen but pressing escape resets the search and pressing enter doesn't do anything. This should be the same as the front page.

## TUI Issues
- clicking space to select brings the cursor all the way back to the top
- searching works kind of but I can't see what I'm typing and once I find what I'm looking for I can't escape search. pressing enter doesn't do anything, pressing escape removes the search filter

## Version Detail Screen - Phase 2 (COMPLETED)
- [x] Add analyzed versions summary panel at top
- [x] Add search functionality (press `/` to filter by name/message)
- [x] Add half-page scrolling (ctrl-d / ctrl-u)
- [x] Fix filtered list index bug
- [x] Update footer with new keybindings
- [x] Add context-aware escape (clear search vs go back)
- [x] Add styling for new components
