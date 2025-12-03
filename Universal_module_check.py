"""
Universal Python Module Inspector
=================================
Comprehensive analysis of any Python module with interactive navigation.

Enhanced Features:
- Universal module detection
- Interactive menu system
- Tree-structured output
- File exploration
- Clean exit handling
- Module validation and error handling
"""

import inspect
import sys
import ast
import os
import signal
import importlib
import pkgutil
from pathlib import Path
from types import ModuleType, FunctionType
from typing import Any, Dict, List, Set, Tuple, Optional
from collections import defaultdict


class UniversalModuleInspector:
    """Universal inspector for any Python module with full interactive capabilities."""
    
    def __init__(self, module_name: Optional[str] = None):
        self.module_name = module_name
        self.module = None
        self.analyzed_classes = set()
        self.analyzed_functions = set()
        self.dependency_graph = defaultdict(set)
        self.exception_graph = defaultdict(set)
        self.instantiation_graph = defaultdict(set)
        self.running = True
        self.current_module_path = None
        
        # Setup signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Initialize module
        if module_name:
            self.load_module(module_name)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n👋 Gracefully shutting down... Goodbye!")
        self.running = False
        sys.exit(0)
    
    def load_module(self, module_name: str) -> bool:
        """Dynamically load and validate a Python module."""
        try:
            print(f"\n🔄 Loading module: {module_name}")
            self.module = importlib.import_module(module_name)
            self.module_name = module_name
            self.current_module_path = getattr(self.module, '__file__', None)
            
            # Reset analysis caches
            self.analyzed_classes.clear()
            self.analyzed_functions.clear()
            self.dependency_graph.clear()
            self.exception_graph.clear()
            self.instantiation_graph.clear()
            
            print(f"✅ Successfully loaded: {module_name}")
            print(f"📁 Module file: {self.current_module_path}")
            return True
            
        except ImportError as e:
            print(f"❌ Failed to import module '{module_name}': {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error loading module '{module_name}': {e}")
            return False
    
    def validate_module_loaded(self) -> bool:
        """Check if a module is currently loaded."""
        if self.module is None:
            print("❌ No module loaded. Please select a module first.")
            return False
        return True
    
    def print_header(self, title: str, level: int = 1):
        """Print formatted section header."""
        if level == 1:
            print(f"\n{'='*80}")
            print(f"  {title}")
            print(f"{'='*80}")
        elif level == 2:
            print(f"\n{'-'*80}")
            print(f"  {title}")
            print(f"{'-'*80}")
        else:
            print(f"\n{'·'*60}")
            print(f"  {title}")
    
    def print_tree_item(self, item: str, depth: int = 0, last: bool = False):
        """Print tree-structured item."""
        prefix = "  " * depth
        branch = "└─ " if last else "├─ "
        print(f"{prefix}{branch}{item}")
    
    def wait_for_user(self):
        """Wait for user to press Enter to continue."""
        input("\n⏎ Press Enter to continue...")
    
    def discover_available_modules(self) -> List[str]:
        """Discover available Python modules in the environment."""
        modules = []
        
        # Standard library modules
        print("\n🔍 Discovering available modules...")
        
        # Check common standard library modules
        stdlib_modules = [
            'os', 'sys', 'json', 're', 'collections', 'datetime', 'math', 
            'random', 'itertools', 'functools', 'threading', 'multiprocessing',
            'subprocess', 'pathlib', 'shutil', 'tempfile', 'logging'
        ]
        
        for mod in stdlib_modules:
            try:
                importlib.import_module(mod)
                modules.append(mod)
            except ImportError:
                pass
        
        # Check installed packages
        try:
            installed_packages = [name for _, name, _ in pkgutil.iter_modules()]
            modules.extend(installed_packages[:20])  # Limit to first 20 for performance
        except:
            pass
        
        return sorted(set(modules))
    
    def select_module_interactive(self):
        """Interactive module selection."""
        modules = self.discover_available_modules()
        
        if not modules:
            print("❌ No modules found in the current environment.")
            return False
        
        self.print_header("MODULE SELECTION", 1)
        
        print("\n📚 Available Modules:")
        print("─"*80)
        for i, mod in enumerate(modules, 1):
            print(f"   {i:2d}. {mod}")
        print("─"*80)
        print("   0. Enter custom module name")
        print("="*80)
        
        try:
            choice = input("\n🔍 Select module (0 for custom, 1-{}): ".format(len(modules))).strip()
            
            if choice == '0':
                custom_module = input("Enter module name: ").strip()
                return self.load_module(custom_module)
            else:
                module_index = int(choice) - 1
                if 0 <= module_index < len(modules):
                    selected_module = modules[module_index]
                    return self.load_module(selected_module)
                else:
                    print("❌ Invalid selection.")
                    return False
                    
        except (ValueError, KeyboardInterrupt):
            print("❌ Invalid input.")
            return False
    
    def inspect_module_structure(self):
        """Inspect module-level structure."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("MODULE STRUCTURE", 1)
        
        print(f"\n📦 Module: {self.module.__name__}")
        print(f"   Version: {getattr(self.module, '__version__', 'N/A')}")
        print(f"   File: {getattr(self.module, '__file__', 'N/A')}")
        print(f"   Package: {getattr(self.module, '__package__', 'N/A')}")
        print(f"   Doc: {getattr(self.module, '__doc__', 'No documentation').strip().split('.')[0] if getattr(self.module, '__doc__', None) else 'No documentation'}")
        
        # Submodules
        self.print_header("Submodules", 3)
        submodules = []
        for name, obj in inspect.getmembers(self.module):
            if inspect.ismodule(obj):
                # Check if it's a submodule of the current module
                if hasattr(obj, '__name__') and obj.__name__.startswith(self.module.__name__ + '.'):
                    submodules.append(name)
        
        if submodules:
            for i, submod in enumerate(sorted(submodules)):
                last = (i == len(submodules) - 1)
                self.print_tree_item(submod, 0, last)
        else:
            print("   No submodules found")
    
    def inspect_imports(self):
        """Inspect module imports."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("MODULE IMPORTS", 2)
        
        imports = {}
        for name, obj in inspect.getmembers(self.module):
            if inspect.ismodule(obj):
                module_name = getattr(obj, '__name__', '')
                # Filter out submodules and standard modules if desired
                if not module_name.startswith(self.module.__name__ + '.'):
                    imports[name] = module_name
        
        if imports:
            print("\n📥 External Imports:")
            for i, (alias, module) in enumerate(sorted(imports.items())):
                last = (i == len(imports) - 1)
                self.print_tree_item(f"{alias} → {module}", 0, last)
        else:
            print("\n📥 No external imports found")
    
    def inspect_classes(self):
        """Inspect all classes in the module."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("CLASS HIERARCHY", 1)
        
        classes = [(name, obj) for name, obj in inspect.getmembers(self.module) 
                  if inspect.isclass(obj) and self._is_module_member(obj)]
        
        if not classes:
            print("No classes found in this module")
            return
        
        # Group by category
        exceptions = []
        regular_classes = []
        
        for name, cls in classes:
            try:
                if issubclass(cls, BaseException):
                    exceptions.append((name, cls))
                else:
                    regular_classes.append((name, cls))
            except:
                regular_classes.append((name, cls))
        
        # Regular Classes
        if regular_classes:
            print("\n🏛️  Regular Classes:")
            for i, (name, cls) in enumerate(sorted(regular_classes)):
                last = (i == len(regular_classes) - 1)
                self._inspect_single_class(name, cls, 0, last)
        
        # Exception Classes
        if exceptions:
            print("\n⚠️  Exception Classes:")
            for i, (name, cls) in enumerate(sorted(exceptions)):
                last = (i == len(exceptions) - 1)
                self._inspect_single_class(name, cls, 0, last)
    
    def _is_module_member(self, obj: Any) -> bool:
        """Check if object belongs to the current module."""
        module_name = getattr(obj, '__module__', '')
        return module_name and (module_name == self.module.__name__ or module_name.startswith(self.module.__name__ + '.'))
    
    def _inspect_single_class(self, name: str, cls: type, depth: int, last: bool):
        """Inspect a single class in detail."""
        if cls in self.analyzed_classes:
            return
        self.analyzed_classes.add(cls)
        
        self.print_tree_item(f"class {name}", depth, last)
        
        # Inheritance (MRO)
        try:
            mro = inspect.getmro(cls)[1:]  # Skip the class itself
            if len(mro) > 1:  # More than just 'object'
                mro_names = ' → '.join([c.__name__ for c in mro if hasattr(c, '__name__') and c.__name__ != 'object'])
                if mro_names:
                    print(f"{'  ' * (depth + 1)}  ├─ 🧬 Inherits: {mro_names}")
        except:
            pass
        
        # Docstring
        if cls.__doc__:
            doc_preview = cls.__doc__.strip().split('\n')[0][:60]
            print(f"{'  ' * (depth + 1)}  ├─ 📝 {doc_preview}...")
        
        # Properties
        properties = []
        try:
            properties = [name for name, obj in inspect.getmembers(cls) 
                         if isinstance(inspect.getattr_static(cls, name, None), property)]
        except:
            pass
            
        if properties:
            print(f"{'  ' * (depth + 1)}  ├─ 🔧 Properties: {', '.join(sorted(properties)[:5])}" + 
                  (f" (+{len(properties)-5} more)" if len(properties) > 5 else ""))
        
        # Methods (excluding private and inherited)
        methods = []
        try:
            for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not method_name.startswith('_') or method_name in ['__init__', '__repr__', '__str__']:
                    if hasattr(cls, '__dict__') and method_name in cls.__dict__:  # Defined in this class
                        methods.append(method_name)
        except:
            pass
        
        if methods:
            print(f"{'  ' * (depth + 1)}  ├─ 🔨 Methods: {', '.join(sorted(methods)[:5])}" + 
                  (f" (+{len(methods)-5} more)" if len(methods) > 5 else ""))
        
        # Class attributes
        attrs = []
        try:
            attrs = [name for name in dir(cls) 
                    if not name.startswith('_') 
                    and name not in methods 
                    and name not in properties
                    and not callable(getattr(cls, name, None))]
        except:
            pass
        
        if attrs:
            print(f"{'  ' * (depth + 1)}  └─ 📊 Attributes: {', '.join(sorted(attrs)[:5])}" +
                  (f" (+{len(attrs)-5} more)" if len(attrs) > 5 else ""))
    
    def inspect_functions(self):
        """Inspect module-level functions."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("MODULE FUNCTIONS", 1)
        
        functions = [(name, obj) for name, obj in inspect.getmembers(self.module) 
                    if inspect.isfunction(obj) and self._is_module_member(obj)]
        
        if functions:
            print("\n🔧 Public Functions:")
            for i, (name, func) in enumerate(sorted(functions)):
                last = (i == len(functions) - 1)
                self._inspect_single_function(name, func, 0, last)
        else:
            print("\n🔧 No module-level functions found")
    
    def _inspect_single_function(self, name: str, func: FunctionType, depth: int, last: bool):
        """Inspect a single function in detail."""
        if func in self.analyzed_functions:
            return
        self.analyzed_functions.add(func)
        
        self.print_tree_item(f"def {name}()", depth, last)
        
        # Signature
        try:
            sig = inspect.signature(func)
            params = [f"{k}" for k in sig.parameters.keys()]
            print(f"{'  ' * (depth + 1)}  ├─ 📋 Parameters: {', '.join(params)}")
        except:
            print(f"{'  ' * (depth + 1)}  ├─ 📋 Parameters: <unable to inspect>")
        
        # Docstring
        if func.__doc__:
            doc_preview = func.__doc__.strip().split('\n')[0][:60]
            print(f"{'  ' * (depth + 1)}  └─ 📝 {doc_preview}...")
    
    def inspect_constants(self):
        """Inspect module constants and global variables."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("CONSTANTS & GLOBALS", 1)
        
        constants = []
        for name, obj in inspect.getmembers(self.module):
            if not name.startswith('_') and not inspect.ismodule(obj) \
               and not inspect.isclass(obj) and not inspect.isfunction(obj):
                try:
                    obj_repr = repr(obj)
                    if len(obj_repr) > 50:
                        obj_repr = obj_repr[:47] + "..."
                    constants.append((name, type(obj).__name__, obj_repr))
                except:
                    constants.append((name, type(obj).__name__, "<unable to represent>"))
        
        if constants:
            print("\n📌 Module-Level Data:")
            for i, (name, type_name, value) in enumerate(sorted(constants)):
                last = (i == len(constants) - 1)
                self.print_tree_item(f"{name}: {type_name} = {value}", 0, last)
        else:
            print("\n📌 No module-level constants found")
    
    def build_dependency_graph(self):
        """Build dependency relationships."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("DEPENDENCY GRAPH", 1)
        
        print("\n🔗 Analyzing dependencies...")
        
        # Analyze imports from module source if available
        if self.current_module_path and os.path.exists(self.current_module_path):
            try:
                with open(self.current_module_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(f"import {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ''
                        for alias in node.names:
                            imports.append(f"from {module} import {alias.name}")
                
                if imports:
                    print("\n📥 Detected Imports:")
                    for i, imp in enumerate(sorted(imports)[:15]):  # Limit display
                        last = (i == min(14, len(imports) - 1))
                        self.print_tree_item(imp, 0, last)
                    if len(imports) > 15:
                        print(f"   ... and {len(imports) - 15} more imports")
                else:
                    print("\n📥 No imports detected in source")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze source for dependencies: {e}")
        else:
            print("⚠️  Source file not available for dependency analysis")
    
    def build_exception_hierarchy(self):
        """Build exception hierarchy."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("EXCEPTION HIERARCHY", 1)
        
        exceptions = [(name, obj) for name, obj in inspect.getmembers(self.module) 
                     if inspect.isclass(obj) and self._is_module_member(obj)]
        
        # Filter for exceptions
        exception_classes = []
        for name, cls in exceptions:
            try:
                if issubclass(cls, BaseException):
                    exception_classes.append((name, cls))
            except:
                pass
        
        if not exception_classes:
            print("⚠️  No exception classes found in this module")
            return
        
        # Build tree structure
        exception_tree = defaultdict(list)
        for name, exc in exception_classes:
            try:
                bases = [b.__name__ for b in exc.__bases__ if hasattr(b, '__name__') and b.__name__ != 'object']
                parent = bases[0] if bases else 'BaseException'
                exception_tree[parent].append(name)
            except:
                pass
        
        print("\n⚠️  Exception Tree:")
        
        def print_exception_tree(parent, depth=0):
            children = exception_tree.get(parent, [])
            for i, child in enumerate(sorted(children)):
                last = (i == len(children) - 1)
                self.print_tree_item(child, depth, last)
                print_exception_tree(child, depth + 1)
        
        # Find root exceptions
        roots_found = False
        for root in exception_tree:
            if root not in [name for names in exception_tree.values() for name in names]:
                roots_found = True
                print_exception_tree(root, 0)
        
        if not roots_found and exception_tree:
            # Fallback: just show all exceptions
            for name, _ in exception_classes:
                self.print_tree_item(name, 0, False)
    
    def inspect_execution_flow(self):
        """Inspect the module's main execution patterns."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("EXECUTION PATTERNS", 1)
        
        print("\n🔍 Analyzing module structure...")
        
        # Check for main execution pattern
        if hasattr(self.module, 'main'):
            print("🎯 Main Function: Found 'main()' function")
        else:
            print("🎯 Main Function: No 'main()' function found")
        
        # Check for common patterns
        patterns = []
        
        # Check if it's a web framework module
        web_indicators = ['get', 'post', 'put', 'delete', 'request', 'route']
        if any(hasattr(self.module, attr) for attr in web_indicators):
            patterns.append("Web/API framework patterns")
        
        # Check if it's a data processing module
        data_indicators = ['load', 'save', 'read', 'write', 'process', 'transform']
        if any(hasattr(self.module, attr) for attr in data_indicators):
            patterns.append("Data processing patterns")
        
        # Check if it's a utility module
        if len([name for name, obj in inspect.getmembers(self.module) if inspect.isfunction(obj)]) > 10:
            patterns.append("Utility/helper functions module")
        
        if patterns:
            print("\n📊 Detected Patterns:")
            for pattern in patterns:
                self.print_tree_item(pattern, 0, False)
        else:
            print("\n📊 No specific patterns detected")
    
    def inspect_module_file_location(self):
        """Inspect module file location and structure."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("MODULE FILE LOCATION", 1)
        
        if not self.current_module_path:
            print("❌ Module file location not available")
            return
        
        module_file = self.current_module_path
        module_dir = os.path.dirname(module_file)
        
        print(f"\n📁 Module Information:")
        self.print_tree_item(f"File: {module_file}", 0, False)
        self.print_tree_item(f"Directory: {module_dir}", 0, True)
        
        # Check if it's a package (has __init__.py)
        if os.path.basename(module_file) == '__init__.py':
            print(f"\n📦 This is a package (__init__.py)")
            package_dir = module_dir
        else:
            package_dir = module_dir
            init_file = os.path.join(module_dir, '__init__.py')
            if os.path.exists(init_file):
                print(f"\n📦 Package __init__.py found")
        
        # List all Python files in the directory
        print("\n📄 Python Files in Module Directory:")
        try:
            py_files = sorted([f for f in os.listdir(package_dir) if f.endswith('.py')])
            for i, file in enumerate(py_files):
                last = (i == len(py_files) - 1)
                file_path = os.path.join(package_dir, file)
                size = os.path.getsize(file_path)
                self.print_tree_item(f"{file} ({size:,} bytes)", 0, last)
        except Exception as e:
            print(f"   ⚠️  Could not list directory: {e}")
    
    def display_file_contents(self, file_path: str, max_lines: int = 50):
        """Display contents of a file with syntax awareness."""
        self.print_header(f"FILE CONTENTS: {os.path.basename(file_path)}", 2)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            print(f"\n📊 File Statistics:")
            self.print_tree_item(f"Total lines: {total_lines}", 0, False)
            self.print_tree_item(f"File size: {os.path.getsize(file_path):,} bytes", 0, True)
            
            print("\n" + "="*80)
            
            display_lines = min(max_lines, total_lines)
            for i, line in enumerate(lines[:display_lines], 1):
                print(f"{i:4d} │ {line.rstrip()}")
            
            if total_lines > max_lines:
                print("="*80)
                print(f"... ({total_lines - max_lines} more lines)")
            
            print("="*80)
            
            # Analyze file structure
            self.analyze_file_structure(file_path)
            
            if total_lines > max_lines:
                print("\n" + "─"*80)
                response = input(f"📖 View full file? (y/n): ").strip().lower()
                if response == 'y':
                    print("\n" + "="*80)
                    for i, line in enumerate(lines, 1):
                        print(f"{i:4d} │ {line.rstrip()}")
                    print("="*80)
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    
    def analyze_file_structure(self, file_path: str):
        """Analyze Python file structure using AST."""
        print("\n" + "─"*80)
        print("  📋 FILE STRUCTURE ANALYSIS")
        print("─"*80)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            imports = []
            functions = []
            classes = []
            constants = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
                elif isinstance(node, ast.FunctionDef):
                    if node.col_offset == 0:  # Top-level function
                        functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    if node.col_offset == 0:  # Top-level class
                        classes.append(node.name)
                elif isinstance(node, ast.Assign):
                    if node.col_offset == 0:  # Top-level assignment
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                constants.append(target.id)
            
            print("\n📦 Imports:")
            if imports:
                for i, imp in enumerate(imports[:10]):
                    last = (i == min(9, len(imports) - 1))
                    self.print_tree_item(imp, 0, last)
                if len(imports) > 10:
                    print(f"   ... and {len(imports) - 10} more")
            else:
                print("   └─ No imports found")
            
            if classes:
                print(f"\n🏛️  Classes ({len(classes)}):")
                for i, cls in enumerate(classes):
                    last = (i == len(classes) - 1)
                    self.print_tree_item(cls, 0, last)
            
            if functions:
                print(f"\n🔧 Functions ({len(functions)}):")
                for i, func in enumerate(functions):
                    last = (i == len(functions) - 1)
                    self.print_tree_item(func, 0, last)
            
            if constants:
                print(f"\n📌 Module-level Variables ({len(constants)}):")
                for i, const in enumerate(constants[:10]):
                    last = (i == min(9, len(constants) - 1))
                    self.print_tree_item(const, 0, last)
                if len(constants) > 10:
                    print(f"   ... and {len(constants) - 10} more")
                    
        except Exception as e:
            print(f"⚠️  Could not analyze file structure: {e}")
    
    def interactive_file_explorer(self):
        """Interactive file explorer for the module directory."""
        if not self.validate_module_loaded() or not self.current_module_path:
            return
        
        module_dir = os.path.dirname(self.current_module_path)
        
        try:
            py_files = sorted([f for f in os.listdir(module_dir) if f.endswith('.py')])
        except Exception as e:
            print(f"❌ Error accessing module directory: {e}")
            return
        
        while self.running:
            self.print_header("FILE EXPLORER", 2)
            
            print("\n📚 Available Python Files:")
            print("─"*80)
            for i, file in enumerate(py_files, 1):
                file_path = os.path.join(module_dir, file)
                size = os.path.getsize(file_path)
                print(f"   {i:2d}. {file:<30s} ({size:>8,} bytes)")
            print("─"*80)
            print(f"    0. Return to main menu")
            
            try:
                choice = input("\n📂 Enter file number to view (0 to exit): ").strip()
                
                if choice == '0':
                    break
                
                file_index = int(choice) - 1
                if 0 <= file_index < len(py_files):
                    selected_file = py_files[file_index]
                    file_path = os.path.join(module_dir, selected_file)
                    self.display_file_contents(file_path)
                    self.wait_for_user()
                else:
                    print("❌ Invalid file number. Please try again.")
                    self.wait_for_user()
                    
            except ValueError:
                print("❌ Please enter a valid number.")
                self.wait_for_user()
            except KeyboardInterrupt:
                print("\n\n👋 Returning to main menu...")
                break
    
    def generate_summary(self):
        """Generate inspection summary."""
        if not self.validate_module_loaded():
            return
            
        self.print_header("INSPECTION SUMMARY", 1)
        
        # Count members
        classes = sum(1 for name, obj in inspect.getmembers(self.module) 
                     if inspect.isclass(obj) and self._is_module_member(obj))
        functions = sum(1 for name, obj in inspect.getmembers(self.module) 
                       if inspect.isfunction(obj) and self._is_module_member(obj))
        
        # Count exceptions separately
        exceptions = 0
        for name, obj in inspect.getmembers(self.module):
            if inspect.isclass(obj) and self._is_module_member(obj):
                try:
                    if issubclass(obj, BaseException):
                        exceptions += 1
                except:
                    pass
        
        print("\n📊 Statistics:")
        self.print_tree_item(f"Module: {self.module.__name__}", 0, False)
        self.print_tree_item(f"Total Classes: {classes}", 0, False)
        self.print_tree_item(f"Total Functions: {functions}", 0, False)
        self.print_tree_item(f"Exception Classes: {exceptions}", 0, False)
        self.print_tree_item(f"Regular Classes: {classes - exceptions}", 0, True)
        
        print("\n✅ Inspection Complete!")
    
    def show_main_menu(self):
        """Display interactive main menu."""
        while self.running:
            current_module = self.module_name if self.module_name else "No module loaded"
            
            self.print_header(f"UNIVERSAL MODULE INSPECTOR - {current_module}", 1)
            
            print("\n📋 Available Inspections:")
            print("─"*80)
            if not self.module:
                print("   1.  Select/Change Module")
            else:
                print("   1.  Select/Change Module (Currently: {})".format(current_module))
                print("   2.  Module Structure")
                print("   3.  Module Imports")
                print("   4.  Class Hierarchy")
                print("   5.  Module Functions")
                print("   6.  Constants & Globals")
                print("   7.  Dependency Graph")
                print("   8.  Exception Hierarchy")
                print("   9.  Execution Patterns")
                print("   10. Module File Location")
                print("   11. File Explorer (Interactive)")
                print("   12. Complete Inspection (All Above)")
                print("   13. Inspection Summary")
            print("─"*80)
            print("   0.  Exit Program")
            print("="*80)
            
            try:
                if self.module:
                    choice = input("\n🔍 Select option (0-13): ").strip()
                else:
                    choice = input("\n🔍 Select option (0-1): ").strip()
                
                if choice == '0':
                    print("\n👋 Thank you for using Universal Module Inspector. Goodbye!")
                    self.running = False
                    break
                elif choice == '1':
                    self.select_module_interactive()
                    if self.module:
                        self.wait_for_user()
                elif self.module:
                    if choice == '2':
                        self.inspect_module_structure()
                        self.wait_for_user()
                    elif choice == '3':
                        self.inspect_imports()
                        self.wait_for_user()
                    elif choice == '4':
                        self.inspect_classes()
                        self.wait_for_user()
                    elif choice == '5':
                        self.inspect_functions()
                        self.wait_for_user()
                    elif choice == '6':
                        self.inspect_constants()
                        self.wait_for_user()
                    elif choice == '7':
                        self.build_dependency_graph()
                        self.wait_for_user()
                    elif choice == '8':
                        self.build_exception_hierarchy()
                        self.wait_for_user()
                    elif choice == '9':
                        self.inspect_execution_flow()
                        self.wait_for_user()
                    elif choice == '10':
                        self.inspect_module_file_location()
                        self.wait_for_user()
                    elif choice == '11':
                        self.interactive_file_explorer()
                    elif choice == '12':
                        self.run_full_inspection()
                        self.wait_for_user()
                    elif choice == '13':
                        self.generate_summary()
                        self.wait_for_user()
                    else:
                        print("❌ Invalid option.")
                        self.wait_for_user()
                else:
                    print("❌ Please select a module first.")
                    self.wait_for_user()
                    
            except ValueError:
                print("❌ Please enter a valid number.")
                self.wait_for_user()
            except KeyboardInterrupt:
                print("\n\n👋 Gracefully shutting down... Goodbye!")
                self.running = False
                break
    
    def run_full_inspection(self):
        """Run complete inspection."""
        if not self.validate_module_loaded():
            return
            
        print("\n" + "="*80)
        print(" "*20 + f"COMPLETE MODULE INSPECTION: {self.module.__name__}")
        print("="*80)
        
        self.inspect_module_structure()
        self.inspect_imports()
        self.inspect_classes()
        self.inspect_functions()
        self.inspect_constants()
        self.build_dependency_graph()
        self.build_exception_hierarchy()
        self.inspect_execution_flow()
        self.inspect_module_file_location()
        self.generate_summary()


def main():
    """Main execution with interactive menu."""
    print("\n" + "="*80)
    print(" "*20 + "UNIVERSAL MODULE INSPECTOR v3.0")
    print(" "*18 + "Enhanced for Any Python Module")
    print("="*80)
    print("\n💡 Tip: Press Ctrl+C anytime to exit gracefully")
    print("="*80)
    
    # Check if module name provided as command line argument
    module_name = None
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
    
    inspector = UniversalModuleInspector(module_name)
    
    # If module was provided via command line and loaded successfully, show menu
    # Otherwise, the menu will handle module selection
    inspector.show_main_menu()


if __name__ == "__main__":
    main()
