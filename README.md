# Python Module Inspector Suite

A collection of three powerful Python module inspection tools, each designed for different use cases and levels of detail. These tools help developers understand the structure, relationships, and components of any Python module through interactive command-line interfaces.

## Overview

This repository contains three distinct module inspectors:

1. **Universal Module Inspector** - Interactive, menu-driven exploration with file browsing
2. **Enhanced Module Inspector** - Advanced connection analysis with AST parsing
3. **Deep Module Inspector** - Comprehensive submodule analysis with detailed class inspection

## Features

### Common Features (All Inspectors)
- Dynamic module loading and validation
- Class hierarchy analysis
- Function signature inspection
- Module structure visualization
- Interactive command-line interface
- Error handling and graceful exits

### Inspector-Specific Features

#### 1. Universal Module Inspector
- Tree-structured output visualization
- Interactive file explorer for module directories
- Complete file content viewing
- AST-based file structure analysis
- Module discovery system
- Execution pattern detection
- Signal handling for clean exits

#### 2. Enhanced Module Inspector
- AST-based connection detection
- Bidirectional relationship mapping (USES/USED BY)
- Type hint extraction and analysis
- Inheritance tree visualization
- Dependency graph generation
- Connection graph with clear directionality
- Export analysis to file

#### 3. Deep Module Inspector
- Deep submodule analysis
- Detailed class attribute extraction
- Instance attribute detection from `__init__`
- Property analysis (readable/writable/deletable)
- Complete usage examples generation
- Comprehensive class method categorization

## Installation

### Requirements
- Python 3.6 or higher
- Standard library only (no external dependencies)

### Setup
```bash
git clone https://github.com/yourusername/python-module-inspector.git
cd python-module-inspector
```

## Usage

### Universal Module Inspector

```bash
python universal_inspector.py [module_name]
```

**Interactive Menu Options:**
- Select/Change Module
- Module Structure
- Module Imports
- Class Hierarchy
- Module Functions
- Constants & Globals
- Dependency Graph
- Exception Hierarchy
- Execution Patterns
- Module File Location
- File Explorer (Interactive)
- Complete Inspection (All Above)
- Inspection Summary

**Example:**
```bash
python universal_inspector.py requests
```

### Enhanced Module Inspector

```bash
python enhanced_inspector.py [module_name]
```

**Interactive Menu Options:**
- Inspect a class (with connections)
- Inspect a function (with connections)
- Show complete connection graph
- Show inheritance tree
- Show module summary
- Load a different module
- Export analysis to file

**Example:**
```bash
python enhanced_inspector.py json
```

### Deep Module Inspector

```bash
python deep_inspector.py [module_name]
```

**Interactive Menu Options:**
- Look at a CLASS from main module
- Look at a SUBMODULE and its classes
- Look at a CLASS inside a SUBMODULE
- Show module summary
- Explore a different module

**Example:**
```bash
python deep_inspector.py os
```

## Choosing the Right Inspector

| Use Case | Recommended Inspector |
|----------|---------------------|
| Browse module files and source code | Universal Inspector |
| Understand class/function relationships | Enhanced Inspector |
| Explore modules with many submodules | Deep Inspector |
| Export analysis for documentation | Enhanced Inspector |
| Learn how to use specific classes | Deep Inspector |
| Analyze dependencies and imports | Universal or Enhanced Inspector |

## Output Examples

### Class Inspection
```
CLASS HIERARCHY
================================================================================

Regular Classes:
└─ class MyClass
   ├─ Inherits: BaseClass
   ├─ Documentation: Brief description...
   ├─ Properties: prop1, prop2
   ├─ Methods: method1, method2, method3
   └─ Attributes: attr1, attr2
```

### Connection Graph
```
CONNECTION GRAPH FOR: MyClass
================================================================================

MyClass (Class)
  USED BY (other components that reference this):
      • OtherClass (Instantiated By)
      • some_function (Accepted By)
  
  USES (components that this references):
      • Inherits From: BaseClass
      • Instantiates: HelperClass
      • Calls Function: utility_function
```

### Module Summary
```
MODULE INFORMATION
--------------------------------------------------------------------------------
  Name: requests
  Location: /path/to/requests/__init__.py
  Description: Python HTTP for Humans.
  Version: 2.31.0

SUMMARY:
  Classes: 15
  Functions: 12
  Submodules: 8
  Constants: 5
```

## Technical Details

### AST-Based Analysis
The Enhanced Inspector uses Python's Abstract Syntax Tree (AST) module for accurate code analysis:
- Precise detection of class instantiation
- Function call tracking
- Import statement analysis
- No false positives from string matching

### File System Integration
The Universal Inspector provides direct access to module source files:
- Automatic file discovery
- Syntax-highlighted viewing
- Line-numbered output
- File size and statistics

### Type Hint Support
All inspectors extract and display type hints when available:
- Parameter type annotations
- Return type annotations
- Property type hints
- Forward reference handling

## Error Handling

All inspectors include comprehensive error handling:
- Module import failures with helpful messages
- Invalid input validation
- Graceful handling of inaccessible attributes
- Keyboard interrupt (Ctrl+C) support
- Clear error messages with suggestions

## Limitations

- Requires modules to be installed in the Python environment
- Cannot analyze compiled-only modules (no source available)
- Some dynamic attributes may not be detected
- C extension modules have limited introspection
- Private members (starting with `_`) are filtered in most views

## Best Practices

1. **Start with Summary**: Run the full analysis first to get an overview
2. **Use Specific Inspectors**: Choose the inspector that matches your needs
3. **Export When Needed**: Use Enhanced Inspector's export feature for documentation
4. **Interactive Exploration**: Use the interactive menus for deep dives
5. **Check Source Files**: Use Universal Inspector's file explorer for implementation details

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- New features
- Documentation improvements
- Performance optimizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built using Python's powerful introspection capabilities:
- `inspect` module for runtime introspection
- `ast` module for static code analysis
- `importlib` for dynamic module loading

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review the code examples in this README

## Roadmap

Planned enhancements:
- JSON/YAML export formats
- Graphical visualization of relationships
- Plugin system for custom analyzers
- Batch analysis of multiple modules
- Integration with documentation generators
- Web-based interface option
