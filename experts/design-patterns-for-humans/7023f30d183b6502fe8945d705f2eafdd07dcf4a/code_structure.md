# Design Patterns For Humans — Code Structure

## Directory Tree

```
design-patterns-for-humans/
└── readme.md          ← The entire project (2321 lines of Markdown + PHP examples)
```

This repository contains exactly one file. There are no subdirectories, no source packages, no configuration files, and no assets tracked in the repository (the banner image referenced in the readme is hosted externally via GitHub's `.github` asset path and is not present in the working tree).

## Single-File Architecture

The entire content of the project lives in `readme.md`. This is an intentional design choice: the project is a reference document, not a software library. The file is 2321 lines long and is divided into the following top-level structural sections:

### 1. Header / Banner (lines 1–18)
- HTML `<p align="center">` block with a `.github/banner.svg` image reference
- Tagline: "Ultra-simplified explanation to design patterns!"
- Author's links to companion project (roadmap.sh) and Twitter

### 2. Navigation Table (lines 21–33)
A three-column Markdown table serving as a clickable table of contents:
- Column 1: Creational Design Patterns (6 entries)
- Column 2: Structural Design Patterns (7 entries)
- Column 3: Behavioral Design Patterns (10 entries)

All entries are anchor links that jump to the corresponding section within the file.

### 3. Introduction (lines 36–61)
- Defines what design patterns are (solutions to recurring problems, not plug-in libraries)
- Wikipedia definition quoted
- "⚠️ Be Careful" anti-misuse section warning against forcing patterns
- Note that examples are in PHP-7 but concepts are language-agnostic
- List of the three pattern categories with anchor links

### 4. Creational Design Patterns Section (lines 63–590)
Category-level introduction explaining that creational patterns are focused on object instantiation. Contains 6 pattern entries:

| Pattern | Approx. Line Range | Key PHP Constructs Demonstrated |
|---|---|---|
| 🏠 Simple Factory | 79–146 | Static factory method, interface + implementation |
| 🏭 Factory Method | 148–234 | Abstract class with abstract factory method, subclass override |
| 🔨 Abstract Factory | 236–359 | Interface-based factory of factories, product families |
| 👷 Builder | 361–466 | Fluent builder with method chaining, `build()` finalizer |
| 🐑 Prototype | 468–535 | PHP `clone` keyword, `__clone()` magic method |
| 💍 Singleton | 537–589 | `final class`, private constructor, static instance, `__clone`/`__wakeup` disabled |

### 5. Structural Design Patterns Section (lines 591–1287)
Category-level introduction explaining that structural patterns concern object composition. Contains 7 pattern entries:

| Pattern | Approx. Line Range | Key PHP Constructs Demonstrated |
|---|---|---|
| 🔌 Adapter | 607–692 | Wrapper class implementing an interface, composition |
| 🚡 Bridge | 694–787 | Two independent inheritance hierarchies composed at runtime |
| 🌿 Composite | 789–920 | Uniform interface for leaf and composite objects |
| ☕ Decorator | 922–1040 | Wrapper chain, each layer delegates and adds behavior |
| 📦 Facade | 1042–1129 | Single simplified class wrapping complex subsystem |
| 🍃 Flyweight | 1131–1210 | Shared object cache (`availableTea[$preference]`), lazy creation |
| 🎱 Proxy | 1212–1286 | Proxy class with same interface, authentication guard, `__call()` mention |

### 6. Behavioral Design Patterns Section (lines 1288–2305)
Category-level introduction explaining that behavioral patterns govern message passing and responsibility assignment. Contains 10 pattern entries:

| Pattern | Approx. Line Range | Key PHP Constructs Demonstrated |
|---|---|---|
| 🔗 Chain of Responsibility | 1308–1409 | Abstract base with `$successor`, `setNext()`, recursive `pay()` |
| 👮 Command | 1411–1525 | Command interface with `execute()`/`undo()`/`redo()`, Invoker class |
| ➿ Iterator | 1527–1631 | PHP SPL `Countable` + `Iterator` interfaces, `foreach` compatibility |
| 👽 Mediator | 1633–1703 | Mediator interface, colleague objects reference mediator |
| 💾 Memento | 1705–1792 | Originator saves/restores state via Memento value object |
| 😎 Observer | 1794–1881 | Observable/Observer interfaces, `attach()` + `notify()` pattern |
| 🏃 Visitor | 1883–2020 | Double-dispatch: `accept(AnimalOperation)` + `visitMonkey/Lion/Dolphin` |
| 💡 Strategy | 2022–2100 | Strategy interface, runtime algorithm selection by context |
| 💢 State | 2102–2191 | State interface returns new state objects, Phone context delegates |
| 📒 Template Method | 2193–2305 | `final` template method calls abstract steps, subclass fills in steps |

### 7. Wrap Up / Contribution / License (lines 2307–2321)
- Brief closing note with future roadmap mention (architectural patterns)
- Contribution guidelines (issues, PRs, spreading the word)
- License badge: Creative Commons BY 4.0

## Pattern Entry Template

Every pattern entry follows a consistent internal structure that serves as the implicit "schema" for the document:

```markdown
[emoji] Pattern Name
--------------
Real world example
> [Analogy in plain language]

In plain words
> [One-sentence essence of the pattern]

Wikipedia says
> [Formal definition]

**Programmatic Example**

[PHP 7 code blocks showing interfaces, concrete classes, and usage]

**When to use?**

[Practical guidance on when to apply this pattern]
```

## Code Organization Patterns

### PHP 7 Class Naming Conventions
All PHP examples use consistent OOP naming:
- Interfaces: noun-based (`Door`, `Lion`, `Command`, `SortStrategy`, `PhoneState`)
- Concrete implementations: descriptive prefix + interface name (`WoodenDoor`, `AfricanLion`, `TurnOn`, `BubbleSortStrategy`, `PhoneStateIdle`)
- Factory classes: noun + `Factory` suffix (`DoorFactory`, `WoodenDoorFactory`)
- Adapter classes: wrapped type + `Adapter` suffix (`WildDogAdapter`)
- Facade classes: subsystem name + `Facade` suffix (`ComputerFacade`)

### Teaching Progression
The document is ordered pedagogically within each category — simpler patterns precede more complex ones. For example, Simple Factory comes before Factory Method, which comes before Abstract Factory, building conceptual scaffolding step by step.

### Cross-Pattern References
The document uses running examples across related patterns to reinforce comparison:
- The `Door` example recurs in Simple Factory → Abstract Factory → Adapter → Proxy
- The `Lion` example recurs in Adapter → Visitor
- Builder examples reference the Factory comparison explicitly in "When to use?"

This technique reinforces the distinctions between related patterns without requiring the reader to memorize isolated definitions.

## Key File Reference

| File | Lines | Role |
|---|---|---|
| `readme.md` | 1–2321 | Complete project content — all 23 patterns with explanations and PHP examples |

No other files exist in the repository at commit `7023f30d183b6502fe8945d705f2eafdd07dcf4a`.
