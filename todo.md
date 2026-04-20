## TODO

- [X] simplify to only use opencode
- [-] enabling/disabling an expert via the tui should send an event and all clients should be updated accordingly
    - [X] currently opening a new session still shows disabled experts. Current solution involves restarting the server
- [ ] add to mcp server ability to update agents, or pick specific version/tag/commit
- [ ] add background agents to workflow (plugin)


- [ ] should notes.md | memory.md | short/long_memory.md be part of the agent class? This way all experts have there own files they update regardless if they are part of a team or not.
    - [ ] under this paradigm each session is just like an object being instantiated, while the agent/expert is like a class in a way. The long term memories are stored at the expert level, under user config not under hivemind itself.
- [ ] the orchestrator itself should have memories that it can keep track of under ~/.config/opencode/
- [ ] where is session data and plans stored today?
- [ ] currently we have 2 ways of running hivemind with and without a server, should we implement 2 strategies for this, since they can effect some of the other features we have implemented
- [ ] should we simplify the mcp server given the new abstraction?


- [ ] update exit as well
```bash
╰─❯ hivemind
▄
█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █▀▀▀ █▀▀█ █▀▀█ █▀▀█
█  █ █  █ █▀▀▀ █  █ █    █  █ █  █ █▀▀▀
▀▀▀▀ █▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀▀▀▀

Session   Bazel aspects explained
Continue  opencode -s ses_253253768ffeoC4SBtauvfRXL7
```



## Wont Do
- [ ] after enabling an expert the session is interrupted and I need to manually continue, ideally it would be nice if this wasn't the case.



can you consult the bazel expert and give me a rundown on how aspects work
