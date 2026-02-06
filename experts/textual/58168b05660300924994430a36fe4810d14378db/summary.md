# Textual: Modern Text User Interface Framework

## Repository Purpose and Goals

Textual is a production-ready Python framework for building sophisticated, cross-platform terminal user interfaces (TUIs) with a modern API. Created by Textualize, Textual aims to bring the best development practices from web frameworks to terminal applications, enabling developers to create rich, interactive applications that run in terminals or web browsers.

The framework's core mission is to provide a developer-friendly API that combines Python's simplicity with modern UI patterns, allowing developers to build maintainable terminal applications with minimal code. Textual abstracts away the complexity of terminal control sequences, screen management, and event handling while providing powerful features like CSS styling, animations, reactive programming, and an extensive widget library.

## Key Features and Capabilities

**Widget Library**: Textual provides over 40 built-in widgets including buttons, data tables, text areas, trees, lists, inputs, checkboxes, radio buttons, progress bars, sparklines, and more. Each widget is fully styled, keyboard-navigable, and follows consistent design patterns.

**CSS Styling System**: A complete CSS implementation adapted for terminal UIs, supporting layouts (grid, horizontal, vertical, dock), colors, borders, padding, margins, alignment, and more. Styles can be defined inline or in external `.tcss` files with live reloading during development.

**Reactive Programming**: A sophisticated reactive attribute system that automatically updates the UI when data changes, eliminating boilerplate code and making state management intuitive and declarative.

**Multi-Platform Support**: Native support for Linux, macOS, and Windows terminals, with specialized drivers for each platform. Applications can also be served to web browsers using `textual serve` or Textual Web.

**Event System**: Comprehensive event handling for keyboard, mouse, focus, mount/unmount, and custom events. Supports event bubbling, message passing between components, and the `@on` decorator for streamlined event handling.

**Layout System**: Flexible layout engines including vertical, horizontal, grid, and dock layouts. Automatic size calculation and constraint-based sizing ensure widgets adapt to terminal dimensions.

**Screen Management**: Multi-screen applications with modal support, screen stacking, and seamless transitions. Each screen can have its own styles, bindings, and command providers.

**Command Palette**: Built-in fuzzy-search command palette (Ctrl+P) that's extensible with custom commands and providers.

**Developer Tools**: The `textual-dev` package provides live console debugging, log viewing, CSS live reload, screenshot capture, and a visual design tool for inspecting widget trees and styles.

**Testing Framework**: Comprehensive testing utilities built on pytest, including snapshot testing for visual regression testing and programmatic control for automated UI testing.

**Rich Integration**: Deep integration with the Rich library for advanced text rendering, syntax highlighting (via tree-sitter), markdown rendering, and pretty printing.

## Primary Use Cases and Target Audience

Textual is designed for Python developers building:

- **Command-line tools and utilities** that need better UX than traditional CLI apps
- **System administration dashboards** for monitoring servers, logs, or infrastructure
- **Data exploration tools** with tables, charts, and interactive visualizations
- **Development tools** like code browsers, debuggers, or build system frontends
- **Configuration interfaces** that are more user-friendly than editing config files
- **Prototypes and demos** that need quick UI development without GUI framework overhead
- **SSH-accessible applications** that run on remote servers without X11
- **Embedded device interfaces** where terminal access is the primary interaction method

The framework targets intermediate to advanced Python developers familiar with async programming (though async is optional) and developers transitioning from web frameworks who want to apply similar patterns to terminal applications.

## High-Level Architecture Overview

Textual follows a component-based architecture with clear separation of concerns:

**Application Layer**: The `App` class serves as the root container and event loop coordinator. It manages screen stacks, message routing, rendering cycles, timers, workers, and the main asyncio event loop.

**Screen Layer**: Screens are top-level containers that represent distinct views. Apps can push/pop screens, creating modal dialogs or navigating between views.

**Widget Layer**: Widgets are the building blocks of UIs. All visual elements inherit from the `Widget` base class, which provides rendering, styling, layout, event handling, and lifecycle management.

**DOM (Document Object Model)**: Textual maintains a tree structure of widgets similar to web DOMs. This enables CSS selectors, query operations, and hierarchical event propagation.

**CSS Engine**: A complete CSS parser and styling engine that compiles stylesheets into optimized style objects. Supports selectors, specificity rules, inheritance, and cascading.

**Layout System**: Pluggable layout engines that calculate widget positions and sizes based on CSS rules and constraints. Layout is computed efficiently with caching and dirty-tracking.

**Driver Layer**: Platform-specific drivers handle terminal I/O, input parsing, and escape sequence generation. Separate drivers for Linux, Windows, Web, and headless (testing) modes.

**Message Pump**: An asyncio-based message queue that routes events, handles priorities, and manages the event lifecycle. All user input and system events flow through this system.

**Reactive System**: A descriptor-based system that tracks attribute changes and triggers callbacks, enabling automatic UI updates and data binding.

**Rendering Pipeline**: A multi-stage pipeline that combines widget renders, applies effects (filters), composites layers, optimizes terminal output, and minimizes redraws using dirty regions.

## Related Projects and Dependencies

**Core Dependencies**:
- **Rich** (≥14.2.0): Text rendering engine powering Textual's output, providing color support, text formatting, and console abstractions
- **markdown-it-py**: Markdown parsing for the Markdown widget
- **typing-extensions**: Backports of newer typing features for older Python versions
- **platformdirs**: Cross-platform directory path resolution

**Optional Dependencies** (syntax extras):
- **tree-sitter**: Fast syntax parsing library
- Multiple tree-sitter language parsers (Python, JavaScript, Rust, Go, etc.) for syntax highlighting in TextArea widgets
- **pygments**: Fallback syntax highlighting engine

**Development Dependencies**:
- **pytest**: Testing framework with asyncio support
- **pytest-textual-snapshot**: Snapshot testing for visual regression testing
- **mypy**: Static type checking
- **mkdocs**: Documentation generation with Material theme
- **black**: Code formatting

**Related Textualize Projects**:
- **textual-dev**: Developer tools package for debugging and development
- **textual-web**: Web serving infrastructure for running Textual apps in browsers
- **rich**: The rendering engine underlying Textual

Textual is a mature, production-ready framework (v7.5.0 as of this analysis) with comprehensive documentation at https://textual.textualize.io/, an active Discord community, and extensive examples demonstrating various use cases.
