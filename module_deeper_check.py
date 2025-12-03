import inspect
import importlib
import sys
import ast
import re
from types import ModuleType, FunctionType
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Set

class DeepModuleInspector:
    def __init__(self):
        """Initialize the inspector."""
        self.module = None
        self.module_name = None
        self.classes = {}
        self.functions = {}
        self.modules = {}
        self.constants = {}
        self.connections = defaultdict(lambda: defaultdict(set))
        self.inheritance_tree = {}
        self.type_hints = {}
        self.reverse_connections = defaultdict(lambda: defaultdict(set))
    
    def load_module(self, module_name):
        """Load a module by name."""
        try:
            self.module = importlib.import_module(module_name)
            self.module_name = module_name
            print(f"✅ Successfully loaded module '{module_name}'")
            return True
        except ImportError as e:
            print(f"❌ Error: Cannot import module '{module_name}'")
            print(f"   {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def get_object_type(self, obj):
        """Determine the type of an object."""
        if inspect.isclass(obj):
            return "CLASS"
        elif inspect.isfunction(obj):
            return "FUNCTION"
        elif inspect.ismethod(obj):
            return "METHOD"
        elif inspect.isbuiltin(obj):
            return "BUILTIN"
        elif inspect.ismodule(obj):
            return "MODULE"
        elif callable(obj):
            return "CALLABLE"
        else:
            return type(obj).__name__.upper()
    
    def analyze_inheritance(self):
        """Analyze class inheritance relationships."""
        for name, cls in self.classes.items():
            bases = []
            for base in cls.__bases__:
                if base.__name__ != 'object':
                    base_module = getattr(base, '__module__', '')
                    if base_module == self.module_name:
                        bases.append(('internal', base.__name__))
                        self.connections[name]['inherits_from'].add(base.__name__)
                        self.reverse_connections[base.__name__]['inherited_by'].add(name)
                    else:
                        bases.append(('external', f"{base_module}.{base.__name__}"))
            
            if bases:
                self.inheritance_tree[name] = bases
    
    def analyze_type_hints(self):
        """Extract type hints from functions and methods."""
        # Analyze functions
        for func_name, func in self.functions.items():
            try:
                sig = inspect.signature(func)
                hints = {}
                
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        hints[param_name] = str(param.annotation)
                
                if sig.return_annotation != inspect.Signature.empty:
                    hints['return'] = str(sig.return_annotation)
                
                if hints:
                    self.type_hints[func_name] = hints
            except:
                pass
        
        # Analyze class methods
        for class_name, cls in self.classes.items():
            for method_name in dir(cls):
                if method_name.startswith('_') and method_name not in ['__init__', '__call__']:
                    continue
                try:
                    method = getattr(cls, method_name)
                    if callable(method):
                        sig = inspect.signature(method)
                        hints = {}
                        
                        for param_name, param in sig.parameters.items():
                            if param_name != 'self' and param.annotation != inspect.Parameter.empty:
                                hints[param_name] = str(param.annotation)
                        
                        if sig.return_annotation != inspect.Signature.empty:
                            hints['return'] = str(sig.return_annotation)
                        
                        if hints:
                            self.type_hints[f"{class_name}.{method_name}"] = hints
                except:
                    pass
    
    def _parse_source_with_ast(self, source_code, component_name):
        """Use AST to accurately parse source code and find real connections."""
        try:
            tree = ast.parse(source_code)
            
            class ConnectionVisitor(ast.NodeVisitor):
                def __init__(self, available_classes, available_functions):
                    self.instantiations = set()
                    self.function_calls = set()
                    self.available_classes = available_classes
                    self.available_functions = available_functions
                
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                        if name in self.available_classes:
                            self.instantiations.add(name)
                        elif name in self.available_functions:
                            self.function_calls.add(name)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            attr_name = node.func.attr
                            if attr_name in self.available_classes:
                                self.instantiations.add(attr_name)
                            elif attr_name in self.available_functions:
                                self.function_calls.add(attr_name)
                    
                    self.generic_visit(node)
            
            visitor = ConnectionVisitor(set(self.classes.keys()), set(self.functions.keys()))
            visitor.visit(tree)
            
            return visitor.instantiations, visitor.function_calls
        except:
            return set(), set()
    
    def analyze_connections(self):
        """Analyze connections between classes, functions, and objects."""
        print("\n🔄 Analyzing connections...")
        
        self.connections.clear()
        self.reverse_connections.clear()
        
        self.analyze_inheritance()
        
        for class_name, cls in self.classes.items():
            self._analyze_class_connections(class_name, cls)
        
        for func_name, func in self.functions.items():
            self._analyze_function_connections(func_name, func)
    
    def _analyze_class_connections(self, class_name, cls):
        """Analyze connections for a specific class using multiple methods."""
        
        try:
            sig = inspect.signature(cls.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    param_type = str(param.annotation)
                    param_type = param_type.replace("'", "").replace('"', '')
                    
                    for other_class in self.classes.keys():
                        if other_class == class_name:
                            continue
                        if re.search(rf'\b{re.escape(other_class)}\b', param_type):
                            self.connections[class_name]['accepts_type'].add(
                                f"{other_class} (in __init__.{param_name})"
                            )
                            self.reverse_connections[other_class]['accepted_by'].add(
                                f"{class_name}.__init__"
                            )
        except:
            pass
        
        try:
            source = inspect.getsource(cls)
            instantiations, function_calls = self._parse_source_with_ast(source, class_name)
            
            for other_class in instantiations:
                if other_class != class_name:
                    self.connections[class_name]['instantiates'].add(other_class)
                    self.reverse_connections[other_class]['instantiated_by'].add(class_name)
            
            for func_name in function_calls:
                self.connections[class_name]['calls_function'].add(func_name)
                self.reverse_connections[func_name]['called_by'].add(class_name)
        except:
            pass
        
        for method_name in dir(cls):
            if method_name.startswith('_') and method_name not in ['__init__', '__call__']:
                continue
            try:
                method = getattr(cls, method_name)
                if callable(method):
                    sig = inspect.signature(method)
                    if sig.return_annotation != inspect.Signature.empty:
                        return_type = str(sig.return_annotation)
                        return_type = return_type.replace("'", "").replace('"', '')
                        
                        for other_class in self.classes.keys():
                            if other_class == class_name:
                                continue
                            if re.search(rf'\b{re.escape(other_class)}\b', return_type):
                                self.connections[class_name]['returns_type'].add(
                                    f"{other_class} (from {method_name})"
                                )
                                self.reverse_connections[other_class]['returned_by'].add(
                                    f"{class_name}.{method_name}"
                                )
            except:
                pass
    
    def _analyze_function_connections(self, func_name, func):
        """Analyze connections for a specific function."""
        
        try:
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    param_type = str(param.annotation)
                    param_type = param_type.replace("'", "").replace('"', '')
                    
                    for class_name in self.classes.keys():
                        if re.search(rf'\b{re.escape(class_name)}\b', param_type):
                            self.connections[func_name]['accepts_type'].add(
                                f"{class_name} (parameter: {param_name})"
                            )
                            self.reverse_connections[class_name]['accepted_by'].add(
                                f"{func_name}({param_name})"
                            )
            
            if sig.return_annotation != inspect.Signature.empty:
                return_type = str(sig.return_annotation)
                return_type = return_type.replace("'", "").replace('"', '')
                
                for class_name in self.classes.keys():
                    if re.search(rf'\b{re.escape(class_name)}\b', return_type):
                        self.connections[func_name]['returns_type'].add(class_name)
                        self.reverse_connections[class_name]['returned_by'].add(func_name)
        except:
            pass
        
        try:
            source = inspect.getsource(func)
            instantiations, function_calls = self._parse_source_with_ast(source, func_name)
            
            for class_name in instantiations:
                self.connections[func_name]['instantiates'].add(class_name)
                self.reverse_connections[class_name]['instantiated_by'].add(func_name)
            
            for other_func in function_calls:
                if other_func != func_name:
                    self.connections[func_name]['calls_function'].add(other_func)
                    self.reverse_connections[other_func]['called_by'].add(func_name)
        except:
            pass
    
    def get_instance_attributes(self, cls):
        """Extract instance attributes from class __init__ and other methods."""
        instance_attrs = {}
        
        try:
            source = inspect.getsource(cls.__init__)
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                attr_name = target.attr
                                if not attr_name.startswith('__'):
                                    instance_attrs[attr_name] = {
                                        'source': '__init__',
                                        'hint': 'Assigned in __init__'
                                    }
        except Exception:
            pass
        
        return instance_attrs
    
    def analyze_structure(self):
        """Analyze the complete module structure."""
        if not self.module:
            print("⚠️  No module loaded. Please load a module first.")
            return
        
        print("\n" + "=" * 100)
        print(f"📊 ANALYZING MODULE: {self.module_name}")
        print("=" * 100)
        
        self.print_module_info()
        
        self.classes = {}
        self.functions = {}
        self.modules = {}
        self.constants = {}
        others = {}
        
        for name in dir(self.module):
            if name.startswith('_') and name not in ['__version__', '__author__', '__file__', '__all__']:
                continue
            
            try:
                obj = getattr(self.module, name)
                
                if hasattr(obj, '__module__'):
                    obj_module = obj.__module__
                    if obj_module and not obj_module.startswith(self.module_name):
                        if not inspect.ismodule(obj):
                            continue
                
                obj_type = self.get_object_type(obj)
                
                if obj_type == "CLASS":
                    self.classes[name] = obj
                elif obj_type in ["FUNCTION", "BUILTIN"]:
                    self.functions[name] = obj
                elif obj_type == "MODULE":
                    self.modules[name] = obj
                elif obj_type in ["STR", "INT", "DICT", "LIST", "TUPLE", "BOOL", "FLOAT"]:
                    self.constants[name] = obj
                else:
                    others[name] = obj
            except Exception:
                pass
        
        print(f"\n📈 SUMMARY:")
        print(f"  🔷 Classes: {len(self.classes)}")
        print(f"  ⚙️ Functions: {len(self.functions)}")
        print(f"  📁 Submodules: {len(self.modules)}")
        print(f"  📌 Constants: {len(self.constants)}")
        if others:
            print(f"  🔸 Others: {len(others)}")
        
        self.analyze_type_hints()
        self.analyze_connections()
        
        self.print_classes(self.classes)
        self.print_functions(self.functions)
        self.print_modules(self.modules)
        self.print_constants(self.constants)
        if others:
            self.print_others(others)
        
        self.print_inheritance_tree()
        self.print_connections_summary()
    
    def print_module_info(self):
        """Print basic module information."""
        print(f"\n📦 MODULE INFORMATION")
        print("-" * 100)
        
        print(f"  Name: {self.module_name}")
        
        if hasattr(self.module, '__file__') and self.module.__file__:
            print(f"  Location: {self.module.__file__}")
        
        if hasattr(self.module, '__doc__') and self.module.__doc__:
            doc = self.module.__doc__.strip().split('\n')[0][:80]
            print(f"  Description: {doc}")
        
        if hasattr(self.module, '__version__'):
            print(f"  Version: {self.module.__version__}")
        
        if hasattr(self.module, '__author__'):
            print(f"  Author: {self.module.__author__}")
    
    def print_classes(self, classes):
        """Print all classes in the module."""
        if not classes:
            return
        
        print(f"\n🔷 CLASSES ({len(classes)})")
        print("-" * 100)
        
        for i, (name, cls) in enumerate(sorted(classes.items()), 1):
            print(f"\n  [{i}] class {name}:")
            
            if hasattr(cls, '__module__'):
                origin = cls.__module__
                print(f"      ↳ Defined in: {origin}")
            
            if name in self.inheritance_tree:
                bases = self.inheritance_tree[name]
                print(f"      ↳ Inherits from: {', '.join([b[1] for b in bases])}")
            
            methods = []
            properties = []
            class_methods = []
            static_methods = []
            
            for m in dir(cls):
                if m.startswith('_') and m not in ['__init__', '__call__', '__str__', '__repr__']:
                    continue
                try:
                    attr = inspect.getattr_static(cls, m)
                    if isinstance(attr, property):
                        properties.append(m)
                    elif isinstance(attr, classmethod):
                        class_methods.append(m)
                    elif isinstance(attr, staticmethod):
                        static_methods.append(m)
                    elif callable(getattr(cls, m)):
                        methods.append(m)
                except:
                    pass
            
            if properties:
                print(f"      ↳ Properties: {len(properties)}")
            if methods:
                print(f"      ↳ Instance Methods: {len(methods)}")
            if class_methods:
                print(f"      ↳ Class Methods: {len(class_methods)}")
            if static_methods:
                print(f"      ↳ Static Methods: {len(static_methods)}")
    
    def print_functions(self, functions):
        """Print all functions in the module."""
        if not functions:
            return
        
        print(f"\n⚙️  FUNCTIONS ({len(functions)})")
        print("-" * 100)
        
        for i, (name, func) in enumerate(sorted(functions.items()), 1):
            try:
                sig = inspect.signature(func)
                params = str(sig)
            except Exception:
                params = "(...)"
            
            print(f"  [{i}] {name}{params}")
            
            if name in self.type_hints:
                hints = self.type_hints[name]
                if 'return' in hints:
                    print(f"      ↳ Returns: {hints['return']}")
    
    def print_modules(self, modules):
        """Print all submodules."""
        if not modules:
            return
        
        print(f"\n📁 SUBMODULES ({len(modules)})")
        print("-" * 100)
        
        for i, (name, mod) in enumerate(sorted(modules.items()), 1):
            print(f"  [{i}] {name}")
            if hasattr(mod, '__file__') and mod.__file__:
                print(f"      ↳ {mod.__file__}")
    
    def print_constants(self, constants):
        """Print module-level constants."""
        if not constants:
            return
        
        print(f"\n📌 CONSTANTS ({len(constants)})")
        print("-" * 100)
        
        for name, value in sorted(constants.items()):
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:50] + "..."
            print(f"  {name}: {type(value).__name__} = {value_str}")
    
    def print_others(self, others):
        """Print other objects."""
        print(f"\n🔸 OTHER OBJECTS ({len(others)})")
        print("-" * 100)
        
        for name, obj in sorted(others.items()):
            print(f"  {name}: {type(obj).__name__}")
    
    def print_inheritance_tree(self):
        """Print class inheritance relationships."""
        if not self.inheritance_tree:
            return
        
        print(f"\n🌳 INHERITANCE TREE")
        print("=" * 100)
        print("Shows which classes inherit from others:\n")
        
        for class_name, bases in sorted(self.inheritance_tree.items()):
            print(f"  {class_name}")
            for base_type, base_name in bases:
                if base_type == 'internal':
                    print(f"    └─ inherits from → {base_name} (in this module)")
                else:
                    print(f"    └─ inherits from → {base_name} (external)")
    
    def print_connections_summary(self):
        """Print a summary of all connections between components."""
        has_any_connections = any(
            any(conn_types.values()) for conn_types in self.connections.values()
        )
        
        if not has_any_connections:
            print(f"\n🔗 No explicit connections detected between module components")
            return
        
        print(f"\n🔗 CONNECTIONS & RELATIONSHIPS")
        print("=" * 100)
        print("Shows how classes and functions interact with each other:\n")
        
        conn_labels = {
            'inherits_from': '  ├─ 📐 Inherits from',
            'accepts_type': '  ├─ 📥 Accepts as parameter',
            'instantiates': '  ├─ 🏗️  Creates instances of',
            'calls_function': '  ├─ 📞 Calls function',
            'returns_type': '  ├─ 📤 Returns type',
        }
        
        for component, conn_types in sorted(self.connections.items()):
            has_connections = any(conn_types.values())
            if not has_connections:
                continue
            
            comp_type = "📦 Class" if component in self.classes else "⚙️  Function"
            print(f"{comp_type}: {component}")
            
            for conn_type, targets in sorted(conn_types.items()):
                if not targets:
                    continue
                
                label = conn_labels.get(conn_type, f'  ├─ {conn_type}')
                
                print(f"{label}:")
                for target in sorted(targets):
                    print(f"  │   └─ {target}")
            
            print()
    
    def show_connection_graph(self, component_name=None):
        """Show detailed connection graph for a specific component or entire module."""
        print("\n" + "=" * 100)
        
        if component_name:
            print(f"🕸️  CONNECTION GRAPH FOR: {component_name}")
        else:
            print(f"🕸️  COMPLETE MODULE CONNECTION GRAPH")
        
        print("=" * 100)
        
        if component_name:
            if component_name not in self.classes and component_name not in self.functions:
                print(f"\n⚠️  Component '{component_name}' not found")
                return
            
            self._print_component_graph(component_name)
        else:
            all_components = list(self.classes.keys()) + list(self.functions.keys())
            for comp in sorted(all_components):
                has_outgoing = any(self.connections.get(comp, {}).values())
                has_incoming = any(self.reverse_connections.get(comp, {}).values())
                
                if has_outgoing or has_incoming:
                    self._print_component_graph(comp)
                    print()
    
    def _print_component_graph(self, component_name):
        """Print connection graph for a single component with clear directionality."""
        comp_type = "Class" if component_name in self.classes else "Function"
        
        print(f"\n{component_name} ({comp_type})")
        
        incoming_conn = self.reverse_connections.get(component_name, {})
        has_incoming = any(incoming_conn.values())
        
        if has_incoming:
            print(f"  ⬇️  USED BY (other components that reference this):")
            for conn_type, sources in sorted(incoming_conn.items()):
                if sources:
                    label = conn_type.replace('_', ' ').title()
                    for source in sorted(sources):
                        print(f"      • {source} ({label})")
        
        outgoing_conn = self.connections.get(component_name, {})
        has_outgoing = any(outgoing_conn.values())
        
        if has_outgoing:
            print(f"  ⬆️  USES (components that this references):")
            for conn_type, targets in sorted(outgoing_conn.items()):
                if targets:
                    label = conn_type.replace('_', ' ').title()
                    for target in sorted(targets):
                        print(f"      • {label}: {target}")
        
        if not has_incoming and not has_outgoing:
            print(f"      • No connections detected")
    
    def _print_class_details(self, class_name, cls):
        """Print detailed class information."""
        print(f"\n🔧 HOW TO CREATE AN INSTANCE")
        print("-" * 100)
        try:
            sig = inspect.signature(cls.__init__)
            params = [p for p in sig.parameters.values() if p.name != 'self']
            
            if not params:
                print(f"  obj = {self.module_name}.{class_name}()")
                print(f"  # No parameters required")
            else:
                print(f"  obj = {self.module_name}.{class_name}(")
                for i, param in enumerate(params):
                    param_str = f"      {param.name}"
                    if param.default != inspect.Parameter.empty:
                        default_repr = repr(param.default) if not callable(param.default) else f"<{type(param.default).__name__}>"
                        param_str += f"={default_repr}"
                    if param.annotation != inspect.Parameter.empty:
                        param_str += f"  # type: {param.annotation}"
                    if i < len(params) - 1:
                        param_str += ","
                    print(param_str)
                print(f"  )")
        except Exception:
            print(f"  obj = {self.module_name}.{class_name}(...)")
            print(f"  # Constructor details not available")
        
        instance_attrs = self.get_instance_attributes(cls)
        
        if instance_attrs:
            print(f"\n📦 INSTANCE ATTRIBUTES ({len(instance_attrs)})")
            print("-" * 100)
            for i, (attr_name, info) in enumerate(sorted(instance_attrs.items()), 1):
                print(f"  [{i}] obj.{attr_name}")
                print(f"      ↳ {info['hint']}")
        
        properties = {}
        methods = {}
        class_methods = {}
        static_methods = {}
        special_methods = {}
        
        for attr_name in dir(cls):
            try:
                attr = inspect.getattr_static(cls, attr_name)
                
                if isinstance(attr, property):
                    properties[attr_name] = attr
                elif isinstance(attr, classmethod):
                    class_methods[attr_name] = attr
                elif isinstance(attr, staticmethod):
                    static_methods[attr_name] = attr
                elif callable(getattr(cls, attr_name)):
                    if attr_name.startswith('__') and attr_name.endswith('__'):
                        special_methods[attr_name] = getattr(cls, attr_name)
                    elif not attr_name.startswith('_'):
                        methods[attr_name] = getattr(cls, attr_name)
            except:
                pass
        
        if properties:
            print(f"\n📊 PROPERTIES ({len(properties)})")
            print("-" * 100)
            for i, name in enumerate(sorted(properties.keys()), 1):
                print(f"  [{i}] obj.{name}")
        
        if methods:
            print(f"\n⚙️  METHODS ({len(methods)})")
            print("-" * 100)
            for i, name in enumerate(sorted(methods.keys()), 1):
                method = methods[name]
                try:
                    sig = inspect.signature(method)
                    print(f"  [{i}] obj.{name}{sig}")
                except:
                    print(f"  [{i}] obj.{name}(...)")
        
        if class_methods:
            print(f"\n🔧 CLASS METHODS ({len(class_methods)})")
            print("-" * 100)
            for i, name in enumerate(sorted(class_methods.keys()), 1):
                print(f"  [{i}] {class_name}.{name}(...)")
        
        if static_methods:
            print(f"\n⚡ STATIC METHODS ({len(static_methods)})")
            print("-" * 100)
            for i, name in enumerate(sorted(static_methods.keys()), 1):
                print(f"  [{i}] {class_name}.{name}(...)")
        
        important_special = ['__str__', '__repr__', '__call__', '__len__', '__iter__', '__getitem__', '__setitem__']
        filtered_special = {k: v for k, v in special_methods.items() if k in important_special}
        
        if filtered_special:
            print(f"\n✨ SPECIAL METHODS ({len(filtered_special)})")
            print("-" * 100)
            for i, name in enumerate(sorted(filtered_special.keys()), 1):
                print(f"  [{i}] obj.{name}(...)")
    
    def inspect_class(self, class_name):
        """Deep inspection of a specific class with connections."""
        if class_name not in self.classes:
            print(f"❌ Class '{class_name}' not found in module.")
            print(f"   Available classes: {', '.join(sorted(self.classes.keys()))}")
            return
        
        cls = self.classes[class_name]
        
        print("\n" + "=" * 100)
        print(f"🔍 DEEP INSPECTION: {class_name}")
        print("=" * 100)
        
        print(f"\n📍 CLASS INFORMATION")
        print("-" * 100)
        print(f"  Name: {class_name}")
        print(f"  Type: {type(cls)}")
        print(f"  Module: {cls.__module__}")
        
        if class_name in self.inheritance_tree:
            print(f"  Inherits from:")
            for base_type, base_name in self.inheritance_tree[class_name]:
                print(f"    • {base_name}")
        
        if hasattr(cls, '__doc__') and cls.__doc__:
            doc = cls.__doc__.strip()
            print(f"  Documentation:")
            for line in doc.split('\n')[:5]:
                print(f"    {line}")
        
        self.show_connection_graph(class_name)
        
        self._print_class_details(class_name, cls)
    
    def inspect_function(self, func_name):
        """Deep inspection of a function with connections."""
        if func_name not in self.functions:
            print(f"❌ Function '{func_name}' not found in module.")
            print(f"   Available functions: {', '.join(sorted(self.functions.keys()))}")
            return
        
        func = self.functions[func_name]
        
        print("\n" + "=" * 100)
        print(f"🔍 DEEP INSPECTION: {func_name}()")
        print("=" * 100)
        
        self.show_connection_graph(func_name)
        
        print(f"\n📍 FUNCTION INFORMATION")
        print("-" * 100)
        print(f"  Name: {func_name}")
        
        try:
            sig = inspect.signature(func)
            print(f"  Signature: {func_name}{sig}")
            
            params = sig.parameters
            if params:
                print(f"\n  Parameters:")
                for param_name, param in params.items():
                    param_info = f"    • {param_name}"
                    if param.annotation != inspect.Parameter.empty:
                        param_info += f": {param.annotation}"
                    if param.default != inspect.Parameter.empty:
                        default_repr = repr(param.default) if not callable(param.default) else f"<{type(param.default).__name__}>"
                        param_info += f" = {default_repr}"
                    print(param_info)
            
            if sig.return_annotation != inspect.Signature.empty:
                print(f"\n  Returns: {sig.return_annotation}")
        except:
            print(f"  Signature: {func_name}(...)")
        
        if func.__doc__:
            print(f"\n  Documentation:")
            doc_lines = func.__doc__.strip().split('\n')[:10]
            for line in doc_lines:
                print(f"    {line}")
    
    def show_menu(self):
        """Show interactive menu."""
        print("\n" + "=" * 100)
        print("🎯 WHAT WOULD YOU LIKE TO DO?")
        print("=" * 100)
        print("\n  1. 🔍 Inspect a class (with connections)")
        print("  2. ⚙️ Inspect a function (with connections)")
        print("  3. 🕸️ Show complete connection graph")
        print("  4. 🌳 Show inheritance tree")
        print("  5. 📊 Show module summary")
        print("  6. 🔄 Load a different module")
        print("  7. 💾 Export analysis to file")
        print("  8. ❌ Exit")
        
        choice = input("\n➤ Enter your choice (1-8): ").strip()
        return choice
    
    def export_to_file(self, filename=None):
        """Export the analysis to a text file."""
        if not filename:
            filename = f"{self.module_name}_analysis.txt"
        
        try:
            from io import StringIO
            
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            self.analyze_structure()
            
            sys.stdout = old_stdout
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(buffer.getvalue())
            
            print(f"\n✅ Analysis exported to: {filename}")
        except Exception as e:
            sys.stdout = old_stdout
            print(f"\n❌ Error exporting to file: {e}")
    
    def interactive_mode(self):
        """Run the inspector in interactive mode."""
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                if not self.classes:
                    print("\n⚠️  No classes found in this module.")
                    continue
                
                print("\n📝 Available classes:")
                for i, name in enumerate(sorted(self.classes.keys()), 1):
                    print(f"  [{i}] {name}")
                
                class_name = input("\n➤ Enter class name (or number): ").strip()
                
                if class_name.isdigit():
                    idx = int(class_name) - 1
                    class_list = sorted(self.classes.keys())
                    if 0 <= idx < len(class_list):
                        class_name = class_list[idx]
                
                if class_name:
                    self.inspect_class(class_name)
            
            elif choice == '2':
                if not self.functions:
                    print("\n⚠️  No functions found in this module.")
                    continue
                
                print("\n📝 Available functions:")
                for i, name in enumerate(sorted(self.functions.keys()), 1):
                    print(f"  [{i}] {name}")
                
                func_name = input("\n➤ Enter function name (or number): ").strip()
                
                if func_name.isdigit():
                    idx = int(func_name) - 1
                    func_list = sorted(self.functions.keys())
                    if 0 <= idx < len(func_list):
                        func_name = func_list[idx]
                
                if func_name:
                    self.inspect_function(func_name)
            
            elif choice == '3':
                self.show_connection_graph()
            
            elif choice == '4':
                self.print_inheritance_tree()
            
            elif choice == '5':
                self.analyze_structure()
            
            elif choice == '6':
                module_name = input("\n➤ Enter new module name: ").strip()
                if module_name:
                    if self.load_module(module_name):
                        self.analyze_structure()
            
            elif choice == '7':
                filename = input("\n➤ Enter filename (press Enter for default): ").strip()
                self.export_to_file(filename if filename else None)
            
            elif choice == '8':
                print("\n👋 Thank you for using Enhanced Module Inspector!")
                print("=" * 100)
                break
            
            else:
                print("❌ Invalid choice. Please enter a number between 1 and 8.")


def main():
    """Main entry point."""
    print("\n" + "=" * 100)
    print("🐍 ENHANCED UNIVERSAL PYTHON MODULE INSPECTOR v2.0")
    print("=" * 100)
    print("\n✨ FEATURES:")
    print("  • Accurate connection detection using AST parsing")
    print("  • Clear distinction between 'USES' and 'USED BY'")
    print("  • Detects: class methods, static methods, special methods")
    print("  • Better type hint analysis")
    print("  • Export analysis to file")
    print("  • Works with ANY Python module!\n")
    
    inspector = DeepModuleInspector()
    
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        print(f"📦 Loading module from command line: {module_name}")
        if inspector.load_module(module_name):
            inspector.analyze_structure()
            inspector.interactive_mode()
        return
    
    while True:
        try:
            module_name = input("📦 Enter module name to analyze (e.g., requests, json, pathlib): ").strip()
            
            if not module_name:
                retry = input("⚠️  No module name provided. Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("\n👋 Goodbye!")
                    break
                continue
            
            if inspector.load_module(module_name):
                inspector.analyze_structure()
                inspector.interactive_mode()
                break
            else:
                retry = input("\n🔄 Would you like to try a different module? (y/n): ").strip().lower()
                if retry != 'y':
                    print("\n👋 Goodbye!")
                    break
        except KeyboardInterrupt: # <--- END OF THE TRY BLOCK
                # This catches Ctrl+C when input() is waiting for module_name
                print("\n\n👋 Program interrupted by user. Exiting gracefully.")
                break

if __name__ == "__main__":
    main()
