# Design Patterns For Humans — APIs and Interfaces

## Overview

This repository is a documentation project, not a software library. It does not expose a programmatic API. Its "interface" is the explanatory text and PHP 7 code examples in `readme.md`. This document catalogs every design pattern covered, including the PHP interfaces, abstract classes, and concrete implementations demonstrated, with code snippets and usage examples drawn directly from the source.

All code examples are in `readme.md`. Line numbers below reference that file at commit `7023f30d183b6502fe8945d705f2eafdd07dcf4a`.

---

## Creational Design Patterns

### Simple Factory (`readme.md` ~lines 79–146)

**Intent:** Hide object creation logic behind a static factory method.

```php
// Interface
interface Door {
    public function getWidth(): float;
    public function getHeight(): float;
}

// Concrete implementation
class WoodenDoor implements Door { ... }

// Factory
class DoorFactory {
    public static function makeDoor($width, $height): Door {
        return new WoodenDoor($width, $height);
    }
}

// Usage
$door = DoorFactory::makeDoor(100, 200);
```

**When to use:** When object creation involves logic beyond simple assignment (avoids repeating creation code everywhere).

---

### Factory Method (`readme.md` ~lines 148–234)

**Intent:** Delegate instantiation to subclasses via an abstract factory method.

```php
abstract class HiringManager {
    abstract protected function makeInterviewer(): Interviewer;

    public function takeInterview() {
        $interviewer = $this->makeInterviewer();
        $interviewer->askQuestions();
    }
}

class DevelopmentManager extends HiringManager {
    protected function makeInterviewer(): Interviewer {
        return new Developer();
    }
}
```

**When to use:** When a class doesn't know at compile time which subclass it needs to create, or when subclasses should control the object type returned.

---

### Abstract Factory (`readme.md` ~lines 236–359)

**Intent:** Provide an interface for creating families of related objects without specifying concrete classes.

```php
interface DoorFactory {
    public function makeDoor(): Door;
    public function makeFittingExpert(): DoorFittingExpert;
}

class WoodenDoorFactory implements DoorFactory {
    public function makeDoor(): Door { return new WoodenDoor(); }
    public function makeFittingExpert(): DoorFittingExpert { return new Carpenter(); }
}
```

**When to use:** When there are interrelated dependencies with non-trivial creation logic (ensures compatible product families).

---

### Builder (`readme.md` ~lines 361–466)

**Intent:** Construct complex objects step by step using a fluent interface, avoiding telescoping constructors.

```php
class BurgerBuilder {
    public function addPepperoni() { $this->pepperoni = true; return $this; }
    public function addLettuce()   { $this->lettuce = true;   return $this; }
    public function addCheese()    { $this->cheese = true;    return $this; }
    public function addTomato()    { $this->tomato = true;    return $this; }
    public function build(): Burger { return new Burger($this); }
}

// Usage — method chaining
$burger = (new BurgerBuilder(14))
    ->addPepperoni()
    ->addLettuce()
    ->addTomato()
    ->build();
```

**When to use:** When an object has many optional configuration steps (multi-step creation vs. Factory's one-step creation).

---

### Prototype (`readme.md` ~lines 468–535)

**Intent:** Create new objects by cloning an existing instance.

```php
$original = new Sheep('Jolly');
$cloned = clone $original;
$cloned->setName('Dolly');
// $original->getName() is still 'Jolly'
```

**Key PHP mechanism:** `clone` keyword; optional `__clone()` magic method to customize deep-copy behavior.

**When to use:** When a similar object already exists and creating from scratch would be expensive.

---

### Singleton (`readme.md` ~lines 537–589)

**Intent:** Ensure only one instance of a class can exist.

```php
final class President {
    private static $instance;
    private function __construct() {}  // prevent direct instantiation
    private function __clone() {}      // prevent cloning
    private function __wakeup() {}     // prevent unserialize

    public static function getInstance(): President {
        if (!self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
}
```

**Warning:** The document explicitly flags Singleton as an anti-pattern when overused — it introduces global state and makes testing difficult.

---

## Structural Design Patterns

### Adapter (`readme.md` ~lines 607–692)

**Intent:** Wrap an incompatible object to make it compatible with an expected interface.

```php
class WildDogAdapter implements Lion {
    protected $dog;
    public function __construct(WildDog $dog) { $this->dog = $dog; }
    public function roar() { $this->dog->bark(); }  // translates the interface
}

// Usage
$hunter->hunt(new WildDogAdapter(new WildDog()));
```

---

### Bridge (`readme.md` ~lines 694–787)

**Intent:** Decouple abstraction from implementation so both can vary independently.

```php
// Abstraction hierarchy
class About implements WebPage {
    protected $theme;
    public function __construct(Theme $theme) { $this->theme = $theme; }
    public function getContent() { return "About page in " . $this->theme->getColor(); }
}

// Implementation hierarchy (injected at runtime)
$about = new About(new DarkTheme());
```

---

### Composite (`readme.md` ~lines 789–920)

**Intent:** Treat individual objects and compositions of objects uniformly.

```php
class Organization {
    protected $employees = [];
    public function addEmployee(Employee $employee) { $this->employees[] = $employee; }
    public function getNetSalaries(): float {
        return array_sum(array_map(fn($e) => $e->getSalary(), $this->employees));
    }
}
// Both Developer and Designer implement Employee — treated identically
```

---

### Decorator (`readme.md` ~lines 922–1040)

**Intent:** Dynamically add behavior to objects by wrapping them in decorator instances.

```php
$someCoffee = new SimpleCoffee();         // cost: 10
$someCoffee = new MilkCoffee($someCoffee); // cost: 12
$someCoffee = new WhipCoffee($someCoffee); // cost: 17
$someCoffee = new VanillaCoffee($someCoffee); // cost: 20
```

Each decorator implements `Coffee` interface, delegates to the inner object, and adds its own cost/description.

---

### Facade (`readme.md` ~lines 1042–1129)

**Intent:** Provide a simple interface to a complex subsystem.

```php
class ComputerFacade {
    public function turnOn() {
        $this->computer->getElectricShock();
        $this->computer->makeSound();
        $this->computer->showLoadingScreen();
        $this->computer->bam();
    }
    public function turnOff() { ... }
}

// Client uses only two methods instead of eight
$computer = new ComputerFacade(new Computer());
$computer->turnOn();
```

---

### Flyweight (`readme.md` ~lines 1131–1210)

**Intent:** Minimize memory use by sharing common state between many fine-grained objects.

```php
class TeaMaker {
    protected $availableTea = [];
    public function make($preference) {
        if (empty($this->availableTea[$preference])) {
            $this->availableTea[$preference] = new KarakTea();  // created once, reused
        }
        return $this->availableTea[$preference];
    }
}
```

---

### Proxy (`readme.md` ~lines 1212–1286)

**Intent:** Provide a surrogate that controls access to another object.

```php
class SecuredDoor implements Door {
    public function open($password) {
        if ($this->authenticate($password)) {
            $this->door->open();
        } else {
            echo "Big no! It ain't possible.";
        }
    }
    private function authenticate($password) { return $password === '$ecr@t'; }
}
```

The document also mentions using `__call()` magic method for a MongoDB ODM proxy implementation.

---

## Behavioral Design Patterns

### Chain of Responsibility (`readme.md` ~lines 1308–1409)

**Intent:** Pass a request along a chain of handlers until one handles it.

```php
abstract class Account {
    protected $successor;
    public function setNext(Account $account) { $this->successor = $account; }
    public function pay(float $amount) {
        if ($this->canPay($amount)) { echo "Paid using " . get_called_class(); }
        elseif ($this->successor) { $this->successor->pay($amount); }
        else { throw new Exception('No account has enough balance'); }
    }
}
// Chain: $bank->setNext($paypal); $paypal->setNext($bitcoin);
```

---

### Command (`readme.md` ~lines 1411–1525)

**Intent:** Encapsulate a request as an object, supporting undo/redo.

```php
interface Command {
    public function execute();
    public function undo();
    public function redo();
}

class TurnOn implements Command {
    public function execute() { $this->bulb->turnOn(); }
    public function undo()    { $this->bulb->turnOff(); }
    public function redo()    { $this->execute(); }
}

$remote = new RemoteControl();
$remote->submit(new TurnOn($bulb));
```

---

### Iterator (`readme.md` ~lines 1527–1631)

**Intent:** Traverse a collection without exposing its internal structure.

```php
class StationList implements Countable, Iterator {
    public function current(): RadioStation { return $this->stations[$this->counter]; }
    public function key() { return $this->counter; }
    public function next() { $this->counter++; }
    public function rewind() { $this->counter = 0; }
    public function valid(): bool { return isset($this->stations[$this->counter]); }
    public function count(): int { return count($this->stations); }
}

foreach($stationList as $station) {
    echo $station->getFrequency();
}
```

Uses PHP's built-in SPL `Iterator` and `Countable` interfaces.

---

### Mediator (`readme.md` ~lines 1633–1703)

**Intent:** Define a mediator object to centralize complex communications between colleagues.

```php
class ChatRoom implements ChatRoomMediator {
    public function showMessage(User $user, string $message) {
        echo date('M d, y H:i') . '[' . $user->getName() . ']:' . $message;
    }
}

class User {
    public function send($message) { $this->chatMediator->showMessage($this, $message); }
}
```

---

### Memento (`readme.md` ~lines 1705–1792)

**Intent:** Capture and externalize an object's state so it can be restored later.

```php
class Editor {
    public function save(): EditorMemento { return new EditorMemento($this->content); }
    public function restore(EditorMemento $memento) { $this->content = $memento->getContent(); }
}

$saved = $editor->save();
$editor->type('And this is third.');
$editor->restore($saved);  // rolls back to saved state
```

---

### Observer (`readme.md` ~lines 1794–1881)

**Intent:** Define a one-to-many dependency so all dependents are notified on state change.

```php
class EmploymentAgency implements Observable {
    public function attach(Observer $observer) { $this->observers[] = $observer; }
    protected function notify(JobPost $jobPosting) {
        foreach ($this->observers as $observer) {
            $observer->onJobPosted($jobPosting);
        }
    }
    public function addJob(JobPost $jobPosting) { $this->notify($jobPosting); }
}
```

---

### Visitor (`readme.md` ~lines 1883–2020)

**Intent:** Add new operations to objects without modifying them (double dispatch).

```php
interface Animal { public function accept(AnimalOperation $operation); }
interface AnimalOperation {
    public function visitMonkey(Monkey $monkey);
    public function visitLion(Lion $lion);
    public function visitDolphin(Dolphin $dolphin);
}

// Adding new behavior (Jump) without touching Animal classes:
class Jump implements AnimalOperation { ... }
$monkey->accept(new Jump());
```

---

### Strategy (`readme.md` ~lines 2022–2100)

**Intent:** Define a family of algorithms, encapsulate each, and make them interchangeable.

```php
class Sorter {
    public function sort(array $dataset): array {
        if (count($dataset) > 5) {
            return $this->sorterBig->sort($dataset);   // QuickSort
        } else {
            return $this->sorterSmall->sort($dataset); // BubbleSort
        }
    }
}
```

---

### State (`readme.md` ~lines 2102–2191)

**Intent:** Allow an object to alter its behavior when its internal state changes.

```php
interface PhoneState {
    public function pickUp(): PhoneState;
    public function hangUp(): PhoneState;
    public function dial(): PhoneState;
}
// Each state returns the next valid state
class PhoneStateIdle implements PhoneState {
    public function pickUp(): PhoneState { return new PhoneStatePickedUp(); }
    public function dial(): PhoneState { throw new Exception("unable to dial in idle state"); }
}
```

---

### Template Method (`readme.md` ~lines 2193–2305)

**Intent:** Define the skeleton of an algorithm in a base class, deferring specific steps to subclasses.

```php
abstract class Builder {
    final public function build() {  // "final" prevents override of the template
        $this->test();
        $this->lint();
        $this->assemble();
        $this->deploy();
    }
    abstract public function test();
    abstract public function lint();
    abstract public function assemble();
    abstract public function deploy();
}
```

---

## Configuration Options and Extension Points

This is a documentation repository — there are no runtime configuration options. However, the content itself documents extension points within each pattern:

- **Factory Method / Abstract Factory** — extension point is creating new subclasses/factories
- **Decorator** — extension point is adding new decorator classes implementing the base interface
- **Visitor** — extension point is adding new `AnimalOperation` implementations without modifying `Animal` classes
- **Strategy** — extension point is adding new `SortStrategy` implementations
- **Template Method** — extension point is subclassing the abstract `Builder` and filling in the abstract steps

## Integration Patterns and Workflows

The document recommends patterns for specific integration scenarios:

| Scenario | Recommended Pattern |
|---|---|
| Need one global config/connection object | Singleton (use sparingly) |
| Building objects with optional parameters | Builder |
| Third-party class with wrong interface | Adapter |
| Add logging/caching without modifying class | Decorator or Proxy |
| Complex subsystem with many classes | Facade |
| Swap algorithms at runtime | Strategy |
| Track undo/redo history | Command + Memento |
| Notify multiple listeners of state changes | Observer |
| Add operations to a class hierarchy without modifying it | Visitor |
