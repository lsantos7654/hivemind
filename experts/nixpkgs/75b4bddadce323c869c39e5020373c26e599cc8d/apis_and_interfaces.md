# Nixpkgs APIs and Interfaces

## Public Entry Points

### Importing nixpkgs (Legacy)

```nix
# Simple import — uses host system
let pkgs = import <nixpkgs> {}; in pkgs.hello

# With configuration
let pkgs = import <nixpkgs> {
  system = "x86_64-linux";
  config = { allowUnfree = true; };
  overlays = [ (final: prev: { myPkg = ...; }) ];
}; in pkgs.curl

# From a path (pinned version)
let pkgs = import /path/to/nixpkgs { config = {}; }; in pkgs.git
```

### Flakes Interface

```nix
# flake.nix
{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }: {
    packages.x86_64-linux.default =
      nixpkgs.legacyPackages.x86_64-linux.hello;

    nixosConfigurations.myHost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [ ./configuration.nix ];
    };
  };
}
```

**Flake outputs provided by nixpkgs:**
- `lib` — Extended nixpkgs lib with `nixos.lib` and `nixosSystem`
- `legacyPackages.<system>` — Full package set per platform
- `nixosModules.notDetected` — Module for undetected hardware
- `nixosModules.readOnlyPkgs` — Module for read-only pkgs argument
- `checks.<system>` — Build and eval checks
- `devShells.<system>.default` — Development environment
- `formatter.<system>` — treefmt code formatter

## Core Package Building API

### `stdenv.mkDerivation`

The fundamental package builder:

```nix
stdenv.mkDerivation {
  pname = "mypackage";
  version = "1.0";

  src = fetchurl {
    url = "https://example.com/mypackage-1.0.tar.gz";
    hash = "sha256-...";
  };

  # Build inputs
  nativeBuildInputs = [ cmake pkg-config ];  # run on build host
  buildInputs = [ openssl zlib ];            # link into output
  propagatedBuildInputs = [ ];               # propagate to dependents

  # Phase customization
  configureFlags = [ "--enable-shared" "--disable-debug" ];
  makeFlags = [ "PREFIX=$(out)" ];

  preBuild = ''
    export HOME=$TMPDIR
  '';

  postInstall = ''
    wrapProgram $out/bin/mypackage --prefix PATH : ${lib.makeBinPath [ bash ]}
  '';

  doCheck = true;
  checkTarget = "test";

  meta = with lib; {
    description = "My package description";
    homepage = "https://example.com/mypackage";
    license = licenses.mit;
    maintainers = [ maintainers.myhandle ];
    platforms = platforms.linux;
  };
}
```

### `callPackage`

Dependency-injecting package importer. Arguments are resolved from the package set by name:

```nix
# In all-packages.nix
myPackage = callPackage ./mypackage.nix { openssl = openssl_3; };

# The package file (mypackage.nix):
{ stdenv, fetchurl, openssl, cmake }:  # auto-injected
stdenv.mkDerivation { ... }
```

### `makeOverridable` and Package Overrides

```nix
# Override package arguments
curl.override { openssl = libressl; }

# Override derivation attributes
hello.overrideAttrs (old: {
  version = "2.12.1";
  src = fetchurl { ... };
  patches = old.patches ++ [ ./my-patch.patch ];
})

# Override with final/prev for fixed-point
curl.overrideAttrs (finalAttrs: prevAttrs: {
  version = "8.5.0";
})
```

## Overlay API

Overlays are functions `final: prev: { ... }` composable via `lib.composeExtensions`:

```nix
# Single overlay
overlays = [
  (final: prev: {
    # Add a new package
    myTool = prev.callPackage ./my-tool { };

    # Override an existing package
    openssl = prev.openssl.overrideAttrs (old: {
      version = "3.2.0";
    });

    # Create a package variant
    pythonEnv = prev.python3.withPackages (ps: [ ps.requests ps.numpy ]);
  })
];

# Composing overlays
lib.composeExtensions overlay1 overlay2
lib.composeManyExtensions [ overlay1 overlay2 overlay3 ]
```

## Key Library Functions (`lib`)

### Attribute Set Functions (`lib.attrsets`)

```nix
lib.attrByPath [ "a" "b" "c" ] "default" attrset
lib.setAttrByPath [ "a" "b" ] value
lib.mapAttrs (name: value: ...) attrset
lib.filterAttrs (name: value: condition) attrset
lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (system: ...)
lib.recursiveUpdate set1 set2
lib.attrNames attrset
lib.attrValues attrset
lib.hasAttr "key" attrset
lib.getAttr "key" attrset
lib.optionalAttrs condition { key = value; }
lib.nameValuePair name value
lib.listToAttrs [ { name = "k"; value = "v"; } ]
lib.intersectAttrs keys attrs
lib.removeAttrs attrs [ "key1" "key2" ]
lib.foldAttrs (item: acc: ...) init attrset
lib.catAttrs "attr" listOfAttrs
```

### List Functions (`lib.lists`)

```nix
lib.map f list
lib.filter pred list
lib.foldl' f init list
lib.foldr f init list
lib.flatten list
lib.concatLists lists
lib.unique list
lib.intersect list1 list2
lib.subtractLists toRemove from
lib.take n list
lib.drop n list
lib.last list
lib.init list
lib.head list
lib.tail list
lib.imap0 (i: v: ...) list
lib.zipLists list1 list2
lib.sortOn f list
lib.partition pred list
lib.count pred list
lib.optional condition value
lib.optionals condition list
lib.toList x          # convert singleton or list to list
lib.concatMap f list
lib.any pred list
lib.all pred list
lib.findFirst pred default list
lib.elem x list
lib.elemAt list n
lib.length list
lib.range from to
lib.reverseList list
```

### String Functions (`lib.strings`)

```nix
lib.concatStrings [ "a" "b" "c" ]
lib.concatStringsSep ", " [ "x" "y" ]
lib.concatMapStrings f list
lib.stringToCharacters "hello"
lib.charToInt "a"
lib.splitString ":" "a:b:c"
lib.hasPrefix "prefix" "prefixmore"
lib.hasSuffix ".nix" "default.nix"
lib.hasInfix "sub" "substring"
lib.removePrefix "pre" "prefix"
lib.removeSuffix ".nix" "default.nix"
lib.escape [ "'" ] "it's"
lib.escapeShellArg arg
lib.escapeShellArgs [ "cmd" "arg with spaces" ]
lib.toUpper "hello"
lib.toLower "HELLO"
lib.trim "  hello  "
lib.normalizePath "/a//b/../c"
lib.sanitizeDerivationName name   # strip invalid chars
lib.nameFromURL url suffix
lib.makeBinPath [ pkg1 pkg2 ]     # :/bin join
lib.makeLibraryPath [ pkg1 pkg2 ] # :/lib join
lib.makeSearchPath "bin" [ pkg1 pkg2 ]
lib.versionOlder "1.0" "2.0"
lib.versionAtLeast "2.0" "1.5"
lib.versions.major "2.3.4"  # "2"
lib.versions.minor "2.3.4"  # "3"
lib.versions.patch "2.3.4"  # "4"
```

### Module System Functions (`lib.modules`, `lib.options`)

```nix
# Declaring options in a module
lib.mkOption {
  type = lib.types.str;
  default = "hello";
  description = "A description of the option.";
  example = "world";
}

lib.mkEnableOption "my service"         # bool option, default false
lib.mkPackageOption pkgs "nginx" { }    # package option with default

# Module merging combinators
lib.mkIf condition config               # conditional config
lib.mkMerge [ config1 config2 ]         # merge multiple configs
lib.mkAfter config                      # low priority merge
lib.mkBefore config                     # high priority merge
lib.mkOverride priority config          # explicit priority
lib.mkDefault config                    # lower than user config (1000)
lib.mkForce config                      # override user config (50)

# Evaluating modules programmatically
lib.evalModules {
  modules = [ module1 module2 ./config.nix ];
  specialArgs = { ... };
}
```

### Type System (`lib.types`)

```nix
lib.types.str           # string
lib.types.lines         # multiline string
lib.types.int           # integer
lib.types.float         # floating point
lib.types.bool          # boolean
lib.types.path          # Nix path
lib.types.package       # derivation
lib.types.attrs         # attribute set (any)
lib.types.anything      # any value
lib.types.raw           # any, no merging
lib.types.nullOr lib.types.str        # nullable
lib.types.either lib.types.str lib.types.int
lib.types.listOf lib.types.str
lib.types.attrsOf lib.types.int
lib.types.lazyAttrsOf lib.types.package
lib.types.submodule { options = { ... }; }
lib.types.enum [ "a" "b" "c" ]
lib.types.oneOf [ lib.types.str lib.types.int ]
lib.types.uniq lib.types.str          # no merging
lib.types.functionTo lib.types.str
lib.types.strMatching "^[a-z]+$"
lib.types.port           # int between 1 and 65535
lib.types.ints.u8        # 0-255
lib.types.ints.u16       # 0-65535
lib.types.ints.positive
lib.types.nonEmptyStr
lib.types.nonEmptyListOf lib.types.str
```

## NixOS Module Interface

Every NixOS module receives these arguments:

```nix
{ config,      # evaluated config (final merged values)
  lib,         # nixpkgs lib
  pkgs,        # package set
  options,     # option declarations tree
  modulesPath, # path to nixos/modules/
  ...          # specialArgs from nixosSystem call
}:
```

A complete module example:

```nix
{ config, lib, pkgs, ... }:
let
  cfg = config.services.myApp;
in {
  options.services.myApp = {
    enable = lib.mkEnableOption "myApp service";
    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
      description = "Port to listen on.";
    };
    package = lib.mkPackageOption pkgs "my-app" { };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.myApp = {
      description = "My Application";
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/my-app --port ${toString cfg.port}";
        DynamicUser = true;
      };
    };

    networking.firewall.allowedTCPPorts = [ cfg.port ];
  };
}
```

## Configuration Options (`config.nix`)

Key global nixpkgs configuration options:

```nix
import <nixpkgs> {
  config = {
    allowUnfree = true;           # allow non-free packages
    allowBroken = false;          # skip broken packages
    allowUnsupportedSystem = false;
    allowAliases = true;          # keep deprecated aliases

    # Per-package unfree allowlist
    allowUnfreePredicate = pkg:
      builtins.elem (lib.getName pkg) [ "vscode" "slack" ];

    # CUDA support
    cudaSupport = true;
    cudaVersion = "12";

    # Package-specific config
    firefox.enableGnomeExtensions = true;

    # Permitted insecure packages
    permittedInsecurePackages = [ "openssl-1.1.1w" ];
  };
}
```

## Scope and `makeScope`

Package scopes group related packages (e.g., Python packages):

```nix
# Creating a scope (e.g., for a plugin ecosystem)
myPlugins = lib.makeScope pkgs.newScope (self: {
  plugin-a = self.callPackage ./plugin-a { };
  plugin-b = self.callPackage ./plugin-b { };
});

# Extending a scope
myPlugins.overrideScope (final: prev: {
  plugin-a = prev.plugin-a.override { ... };
})
```

## Special Package Attributes

```nix
# Cross-compilation package sets
pkgsCross.aarch64-multiplatform.hello
pkgsCross.raspberryPi.gcc
pkgsStatic.curl            # static linking
pkgsMusl.openssl           # musl libc

# Python package environment
python3.withPackages (ps: [ ps.requests ps.numpy ps.pandas ])

# Kernel variants
linuxPackages.kernel
linuxPackages_latest.kernel
linuxPackages_hardened.kernel

# Development shell
mkShell {
  packages = [ cmake python3 nodejs ];
  shellHook = ''
    export MY_VAR=value
  '';
}
```

## Integration Patterns

### Home Manager Integration

```nix
# flake.nix
inputs.home-manager.inputs.nixpkgs.follows = "nixpkgs";

# In home-manager module:
home.packages = with pkgs; [ git curl vim ];
programs.git.enable = true;
```

### Custom Package Sets via Overlays

```nix
# ~/.config/nixpkgs/overlays/my-overlay.nix
final: prev: {
  myCustomApp = prev.callPackage /path/to/my-app { };

  # Pin a package to a specific version
  openssl = prev.openssl_3_1;
}
```

### `nixosSystem` for Full System Configuration

```nix
nixpkgs.lib.nixosSystem {
  system = "x86_64-linux";
  modules = [
    ./hardware-configuration.nix
    ./configuration.nix
    ({ pkgs, ... }: {
      environment.systemPackages = [ pkgs.vim pkgs.git ];
      services.openssh.enable = true;
    })
  ];
  specialArgs = { myCustomArg = "value"; };
}
```
