import inspect
import importlib
import sys
from types import ModuleType

class DeepModuleInspector:
    def __init__(self):
        """Initialize the inspector."""
        self.module = None
        self.module_name = None
        self.classes = {}
        self.functions = {}
        self.modules = {}
        self.constants = {}
        self.all_submodules = {}  # Store all submodule data
    
    def load_module(self, module_name):
        """Load a module by name."""
        try:
            self.module = importlib.import_module(module_name)
            self.module_name = module_name
            print(f"\n✅ Great! We loaded '{module_name}' successfully!")
            print(f"🎉 Now let's explore what's inside...")
            return True
        except ImportError as e:
            print(f"\n❌ Oops! We can't find a module called '{module_name}'")
            print(f"💡 Make sure it's installed. Try: pip install {module_name}")
            return False
        except Exception as e:
            print(f"\n❌ Something went wrong: {e}")
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
    
    def analyze_class_details(self, cls):
        """Deep analysis of a class - extract all details."""
        details = {
            'properties': {},
            'methods': {},
            'instance_attrs': {},
            'class_attrs': {},
            'init_params': []
        }
        
        # Get __init__ parameters
        try:
            sig = inspect.signature(cls.__init__)
            details['init_params'] = [p for p in sig.parameters.values() if p.name != 'self']
        except:
            pass
        
        # Get instance attributes from __init__
        details['instance_attrs'] = self.get_instance_attributes(cls)
        
        # Get properties, methods, and class attributes
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            
            try:
                attr = inspect.getattr_static(cls, attr_name)
                if isinstance(attr, property):
                    details['properties'][attr_name] = {
                        'readable': attr.fget is not None,
                        'writable': attr.fset is not None,
                        'deletable': attr.fdel is not None
                    }
                elif callable(getattr(cls, attr_name)):
                    method = getattr(cls, attr_name)
                    try:
                        sig = inspect.signature(method)
                        params = [p.name for p in sig.parameters.values() if p.name != 'self']
                        details['methods'][attr_name] = params
                    except:
                        details['methods'][attr_name] = []
                else:
                    # Class-level attribute
                    details['class_attrs'][attr_name] = attr
            except:
                pass
        
        return details
    
    def analyze_submodule(self, submodule_name, submodule_obj):
        """Analyze a submodule in detail."""
        sub_data = {
            'name': submodule_name,
            'classes': {},
            'functions': {},
            'constants': {},
            'description': None,
            'file_location': None,
            'class_details': {}  # NEW: Store detailed class info
        }
        
        # Get basic info
        if hasattr(submodule_obj, '__doc__') and submodule_obj.__doc__:
            sub_data['description'] = submodule_obj.__doc__.strip().split('\n')[0][:100]
        
        if hasattr(submodule_obj, '__file__') and submodule_obj.__file__:
            sub_data['file_location'] = submodule_obj.__file__
        
        # Categorize members
        try:
            for name in dir(submodule_obj):
                if name.startswith('_'):
                    continue
                
                try:
                    obj = getattr(submodule_obj, name)
                    obj_type = self.get_object_type(obj)
                    
                    if obj_type == "CLASS":
                        sub_data['classes'][name] = obj
                        # NEW: Deep analyze each class
                        sub_data['class_details'][name] = self.analyze_class_details(obj)
                    elif obj_type in ["FUNCTION", "BUILTIN"]:
                        sub_data['functions'][name] = obj
                    elif obj_type in ["STR", "INT", "DICT", "LIST", "TUPLE", "BOOL", "FLOAT"]:
                        sub_data['constants'][name] = obj
                except:
                    pass
        except:
            pass
        
        return sub_data
    
    def analyze_structure(self):
        """Analyze the complete module structure."""
        if not self.module:
            print("\n⚠️  Oops! We need to load a module first.")
            print("💡 Let's go back and load one!")
            return
        
        print("\n" + "=" * 100)
        print(f"🔬 EXPLORING MODULE: {self.module_name}")
        print("=" * 100)
        print("📚 Think of this like opening a toolbox - let's see what tools are inside!\n")
        
        # Module info
        self.print_module_info()
        
        # Categorize members
        self.classes = {}
        self.functions = {}
        self.modules = {}
        self.constants = {}
        self.all_submodules = {}
        others = {}
        
        for name in dir(self.module):
            if name.startswith('_') and name not in ['__version__', '__author__', '__file__']:
                continue
            
            try:
                obj = getattr(self.module, name)
                obj_type = self.get_object_type(obj)
                
                if obj_type == "CLASS":
                    self.classes[name] = obj
                elif obj_type in ["FUNCTION", "BUILTIN"]:
                    self.functions[name] = obj
                elif obj_type == "MODULE":
                    self.modules[name] = obj
                    # Deep analyze submodules
                    print(f"🔍 Analyzing submodule: {name}...")
                    self.all_submodules[name] = self.analyze_submodule(name, obj)
                elif obj_type in ["STR", "INT", "DICT", "LIST", "TUPLE", "BOOL", "FLOAT"]:
                    self.constants[name] = obj
                else:
                    others[name] = obj
            except Exception:
                pass
        
        # Print summary
        print(f"\n📊 WHAT WE FOUND:")
        print("=" * 100)
        print(f"  🏗️  Classes (Blueprints for objects): {len(self.classes)}")
        print(f"  ⚙️  Functions (Tools you can use): {len(self.functions)}")
        print(f"  📦 Submodules (Smaller toolboxes inside): {len(self.modules)}")
        print(f"  📌 Constants (Fixed values): {len(self.constants)}")
        if others:
            print(f"  🔸 Other stuff: {len(others)}")
        
        # Print categorized analysis
        self.print_classes(self.classes)
        self.print_functions(self.functions)
        self.print_submodules_detailed()
        self.print_constants(self.constants)
        if others:
            self.print_others(others)
    
    def print_module_info(self):
        """Print basic module information."""
        print(f"📦 ABOUT THIS MODULE")
        print("-" * 100)
        
        print(f"  Name: {self.module_name}")
        print(f"  💡 This is like the name on the toolbox")
        
        if hasattr(self.module, '__file__') and self.module.__file__:
            print(f"\n  Location: {self.module.__file__}")
            print(f"  💡 This is where Python keeps this module on your computer")
        
        if hasattr(self.module, '__doc__') and self.module.__doc__:
            doc = self.module.__doc__.strip().split('\n')[0][:100]
            print(f"\n  What it does: {doc}")
        
        if hasattr(self.module, '__version__'):
            print(f"\n  Version: {self.module.__version__}")
            print(f"  💡 Like version 1.0, 2.0 of an app")
    
    def print_classes(self, classes):
        """Print all classes in the module."""
        if not classes:
            return
        
        print(f"\n🏗️  CLASSES - Blueprints for Creating Objects ({len(classes)})")
        print("=" * 100)
        print("💡 Think of classes like cookie cutters - you use them to make objects!")
        print()
        
        for i, (name, cls) in enumerate(sorted(classes.items()), 1):
            print(f"  [{i}] 🍪 {name}")
            print(f"      ↳ Use this to create: {self.module_name}.{name}()")
            
            # Count useful things
            methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m, None))]
            properties = []
            
            for m in dir(cls):
                if m.startswith('_'):
                    continue
                try:
                    if isinstance(inspect.getattr_static(cls, m), property):
                        properties.append(m)
                except:
                    pass
            
            if methods:
                print(f"      ↳ Has {len(methods)} things you can do (methods)")
            if properties:
                print(f"      ↳ Has {len(properties)} things you can check (properties)")
            print()
    
    def print_functions(self, functions):
        """Print all functions in the module."""
        if not functions:
            return
        
        print(f"⚙️  FUNCTIONS - Ready-to-Use Tools ({len(functions)})")
        print("=" * 100)
        print("💡 Functions are like tools - just pick one and use it!")
        print()
        
        for i, (name, func) in enumerate(sorted(functions.items()), 1):
            try:
                sig = inspect.signature(func)
                params = [p.name for p in sig.parameters.values()]
                if params:
                    params_str = ", ".join(params)
                    print(f"  [{i}] 🔧 {name}({params_str})")
                else:
                    print(f"  [{i}] 🔧 {name}()")
            except Exception:
                print(f"  [{i}] 🔧 {name}(...)")
            
            # Show what it does
            if hasattr(func, '__doc__') and func.__doc__:
                doc = func.__doc__.strip().split('\n')[0][:70]
                if doc:
                    print(f"      ↳ What it does: {doc}")
            print()
    
    def print_submodules_detailed(self):
        """Print detailed information about submodules."""
        if not self.all_submodules:
            return
        
        print(f"📦 SUBMODULES - Smaller Toolboxes Inside ({len(self.all_submodules)})")
        print("=" * 100)
        print("💡 Submodules are like drawers in your toolbox - each has its own tools!")
        print()
        
        for i, (name, sub_data) in enumerate(sorted(self.all_submodules.items()), 1):
            print(f"  [{i}] 📂 {name}")
            print(f"      ↳ Import it: import {self.module_name}.{name}")
            
            if sub_data['description']:
                print(f"      ↳ What it does: {sub_data['description']}")
            
            # Show what's inside
            total_items = len(sub_data['classes']) + len(sub_data['functions']) + len(sub_data['constants'])
            
            if total_items > 0:
                print(f"\n      📊 What's inside this submodule:")
                
                if sub_data['classes']:
                    print(f"         🏗️  {len(sub_data['classes'])} Classes:")
                    for class_name in list(sub_data['classes'].keys())[:5]:
                        # Show class with details
                        details = sub_data['class_details'].get(class_name, {})
                        methods_count = len(details.get('methods', {}))
                        props_count = len(details.get('properties', {}))
                        
                        info_parts = []
                        if methods_count > 0:
                            info_parts.append(f"{methods_count} methods")
                        if props_count > 0:
                            info_parts.append(f"{props_count} properties")
                        
                        info_str = f" [{', '.join(info_parts)}]" if info_parts else ""
                        print(f"            • {class_name}{info_str}")
                    
                    if len(sub_data['classes']) > 5:
                        print(f"            ... and {len(sub_data['classes']) - 5} more")
                
                if sub_data['functions']:
                    print(f"         ⚙️  {len(sub_data['functions'])} Functions:")
                    for func_name in list(sub_data['functions'].keys())[:5]:
                        print(f"            • {func_name}()")
                    if len(sub_data['functions']) > 5:
                        print(f"            ... and {len(sub_data['functions']) - 5} more")
                
                if sub_data['constants']:
                    print(f"         📌 {len(sub_data['constants'])} Constants")
            else:
                print(f"      ↳ This submodule might have hidden items starting with _")
            
            print()
    
    def print_constants(self, constants):
        """Print module-level constants."""
        if not constants:
            return
        
        print(f"📌 CONSTANTS - Fixed Values You Can Use ({len(constants)})")
        print("=" * 100)
        print("💡 These are like having pre-written answers - just use them!")
        print()
        
        for name, value in sorted(constants.items()):
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:50] + "..."
            print(f"  • {name} = {value_str}")
            print(f"    Type: {type(value).__name__}")
            print()
    
    def print_others(self, others):
        """Print other objects."""
        print(f"🔸 OTHER ITEMS ({len(others)})")
        print("=" * 100)
        
        for name, obj in sorted(others.items()):
            print(f"  • {name} ({type(obj).__name__})")
    
    def get_instance_attributes(self, cls):
        """Extract instance attributes from class."""
        instance_attrs = {}
        
        try:
            init_source = inspect.getsource(cls.__init__)
            for line in init_source.split('\n'):
                if 'self.' in line and '=' in line:
                    parts = line.split('self.')[1].split('=')
                    if len(parts) >= 2:
                        attr_name = parts[0].strip().split()[0].split('(')[0]
                        if attr_name and not attr_name.startswith('_'):
                            instance_attrs[attr_name] = {
                                'source': '__init__',
                                'hint': 'Set when object is created'
                            }
        except:
            pass
        
        return instance_attrs
    
    def inspect_class_detailed(self, class_name, cls, module_path):
        """Deep inspection of a specific class with full details."""
        print("\n" + "=" * 100)
        print(f"🔍 EXPLORING: {class_name}")
        print("=" * 100)
        print(f"💡 This is a blueprint for making {class_name} objects!\n")
        
        # Show documentation
        if hasattr(cls, '__doc__') and cls.__doc__:
            doc = cls.__doc__.strip()
            print(f"📖 WHAT IS IT?")
            print("-" * 100)
            for line in doc.split('\n')[:5]:
                if line.strip():
                    print(f"  {line}")
        
        # Show how to create it
        print(f"\n🎨 HOW TO CREATE ONE")
        print("-" * 100)
        try:
            sig = inspect.signature(cls.__init__)
            params = [p for p in sig.parameters.values() if p.name != 'self']
            
            if not params:
                print(f"  ✨ Super easy! No ingredients needed:")
                print(f"  obj = {module_path}.{class_name}()")
            else:
                print(f"  ✨ You need these ingredients:")
                print(f"  obj = {module_path}.{class_name}(")
                for param in params:
                    param_str = f"      {param.name}"
                    if param.default != inspect.Parameter.empty:
                        param_str += f" = {param.default}"
                    print(param_str)
                print(f"  )")
        except:
            print(f"  obj = {module_path}.{class_name}(...)")
        
        # Get all the details
        properties = {}
        methods = {}
        instance_attrs = {}
        
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
            
            try:
                attr = inspect.getattr_static(cls, attr_name)
                if isinstance(attr, property):
                    properties[attr_name] = attr
                elif callable(getattr(cls, attr_name)):
                    methods[attr_name] = getattr(cls, attr_name)
            except:
                pass
        
        instance_attrs = self.get_instance_attributes(cls)
        
        # Show instance attributes
        if instance_attrs:
            print(f"\n📦 THINGS YOUR OBJECT WILL HAVE ({len(instance_attrs)})")
            print("-" * 100)
            print(f"  💡 After you create an object, it will have these things:")
            print()
            for attr_name in sorted(instance_attrs.keys()):
                print(f"  • obj.{attr_name}")
                print(f"    ↳ You can read and use this")
        
        # Show properties
        if properties:
            print(f"\n🔮 MAGICAL PROPERTIES ({len(properties)})")
            print("-" * 100)
            print(f"  💡 These look like regular things but are computed automatically:")
            print()
            for name in sorted(properties.keys()):
                prop = properties[name]
                print(f"  • obj.{name}")
                
                can_read = prop.fget is not None
                can_write = prop.fset is not None
                
                if can_read and can_write:
                    print(f"    ↳ You can read it AND change it")
                elif can_read:
                    print(f"    ↳ You can read it (but not change it)")
        
        # Show methods
        if methods:
            print(f"\n⚙️  THINGS YOU CAN DO ({len(methods)})")
            print("-" * 100)
            print(f"  💡 These are actions your object can perform:")
            print()
            for name in sorted(methods.keys()):
                try:
                    sig = inspect.signature(methods[name])
                    params = [p.name for p in sig.parameters.values() if p.name != 'self']
                    if params:
                        print(f"  • obj.{name}({', '.join(params)})")
                    else:
                        print(f"  • obj.{name}()")
                except:
                    print(f"  • obj.{name}(...)")
        
        # Complete example
        print(f"\n🎯 COMPLETE EXAMPLE - Copy and Try This!")
        print("=" * 100)
        print(f"# Step 1: Import the module")
        print(f"import {module_path.split('.')[0]}")
        if '.' in module_path:
            print(f"# or more specifically:")
            print(f"from {'.'.join(module_path.split('.')[:-1])} import {module_path.split('.')[-1]}")
        print()
        print(f"# Step 2: Create your object")
        try:
            sig = inspect.signature(cls.__init__)
            params = [p for p in sig.parameters.values() if p.name != 'self']
            if not params:
                print(f"my_obj = {module_path}.{class_name}()")
            else:
                print(f"my_obj = {module_path}.{class_name}(")
                for param in params[:3]:
                    print(f"    {param.name}=...,  # Add your value here")
                print(f")")
        except:
            print(f"my_obj = {module_path}.{class_name}(...)")
        
        print()
        print(f"# Step 3: Use it!")
        if instance_attrs:
            attr = list(instance_attrs.keys())[0]
            print(f"print(my_obj.{attr})  # See what's inside")
        if methods:
            method = list(methods.keys())[0]
            print(f"my_obj.{method}()  # Do something cool")
    
    def inspect_class(self, class_name):
        """Deep inspection of a specific class from main module."""
        if class_name not in self.classes:
            print(f"\n❌ Hmm, we can't find a class called '{class_name}' in the main module")
            print(f"\n💡 Available classes in main module:")
            for name in sorted(self.classes.keys()):
                print(f"   • {name}")
            return
        
        cls = self.classes[class_name]
        self.inspect_class_detailed(class_name, cls, self.module_name)
    
    def inspect_submodule_class(self, submodule_name, class_name):
        """Inspect a class from a submodule."""
        if submodule_name not in self.all_submodules:
            print(f"\n❌ We can't find a submodule called '{submodule_name}'")
            return
        
        sub_data = self.all_submodules[submodule_name]
        
        if class_name not in sub_data['classes']:
            print(f"\n❌ We can't find a class called '{class_name}' in submodule '{submodule_name}'")
            print(f"\n💡 Available classes in this submodule:")
            for name in sorted(sub_data['classes'].keys()):
                print(f"   • {name}")
            return
        
        cls = sub_data['classes'][class_name]
        module_path = f"{self.module_name}.{submodule_name}"
        self.inspect_class_detailed(class_name, cls, module_path)
    
    def inspect_submodule(self, submodule_name):
        """Inspect a specific submodule in detail."""
        if submodule_name not in self.all_submodules:
            print(f"\n❌ We can't find a submodule called '{submodule_name}'")
            print(f"\n💡 Available submodules:")
            for name in sorted(self.all_submodules.keys()):
                print(f"   • {name}")
            return
        
        sub_data = self.all_submodules[submodule_name]
        
        print("\n" + "=" * 100)
        print(f"🔍 EXPLORING SUBMODULE: {submodule_name}")
        print("=" * 100)
        print(f"💡 This is a smaller toolbox inside {self.module_name}!\n")
        
        print(f"📦 HOW TO USE IT")
        print("-" * 100)
        print(f"  import {self.module_name}.{submodule_name}")
        print(f"  # Now you can use: {self.module_name}.{submodule_name}.something()")
        
        if sub_data['description']:
            print(f"\n📖 WHAT IT DOES")
            print("-" * 100)
            print(f"  {sub_data['description']}")
        
        # Show classes with detailed counts
        if sub_data['classes']:
            print(f"\n🏗️  CLASSES IN THIS SUBMODULE ({len(sub_data['classes'])})")
            print("-" * 100)
            print("💡 Type the class name to see full details!")
            print()
            for i, (name, cls) in enumerate(sorted(sub_data['classes'].items()), 1):
                details = sub_data['class_details'].get(name, {})
                methods_count = len(details.get('methods', {}))
                props_count = len(details.get('properties', {}))
                
                print(f"  [{i}] {name}")
                print(f"      ↳ Create with: {self.module_name}.{submodule_name}.{name}()")
                
                if methods_count > 0 or props_count > 0:
                    parts = []
                    if methods_count > 0:
                        parts.append(f"{methods_count} methods")
                    if props_count > 0:
                        parts.append(f"{props_count} properties")
                    print(f"      ↳ Has: {', '.join(parts)}")
                print()
        
        # Show functions
        if sub_data['functions']:
            print(f"⚙️  FUNCTIONS IN THIS SUBMODULE ({len(sub_data['functions'])})")
            print("-" * 100)
            for i, (name, func) in enumerate(sorted(sub_data['functions'].items()), 1):
                print(f"  [{i}] {name}()")
                print(f"      ↳ Use: {self.module_name}.{submodule_name}.{name}()")
                
                if hasattr(func, '__doc__') and func.__doc__:
                    doc = func.__doc__.strip().split('\n')[0][:60]
                    if doc:
                        print(f"      ↳ {doc}")
                print()
        
        # Show constants
        if sub_data['constants']:
            print(f"📌 CONSTANTS IN THIS SUBMODULE ({len(sub_data['constants'])})")
            print("-" * 100)
            for name, value in sorted(sub_data['constants'].items()):
                value_str = str(value)
                if len(value_str) > 40:
                    value_str = value_str[:40] + "..."
                print(f"  • {name} = {value_str}")
        
        # Example
        print(f"\n🎯 EXAMPLE - Try This!")
        print("=" * 100)
        print(f"import {self.module_name}.{submodule_name}")
        print()
        if sub_data['functions']:
            func_name = list(sub_data['functions'].keys())[0]
            print(f"# Use a function")
            print(f"result = {self.module_name}.{submodule_name}.{func_name}()")
        if sub_data['classes']:
            class_name = list(sub_data['classes'].keys())[0]
            print(f"\n# Create an object")
            print(f"obj = {self.module_name}.{submodule_name}.{class_name}()")
    
    def show_menu(self):
        """Show interactive menu."""
        print("\n" + "=" * 100)
        print("🎮 WHAT DO YOU WANT TO EXPLORE?")
        print("=" * 100)
        print("\n  1. 🏗️ Look at a CLASS from main module")
        print("  2. 📦 Look at a SUBMODULE and its classes")
        print("  3. 🔎 Look at a CLASS inside a SUBMODULE")
        print("  4. 📊 Show me everything again (summary)")
        print("  5. 🔄 Explore a different module")
        print("  6. 🚪 I'm done - Exit")
        
        choice = input("\n➤ Pick a number (1-6): ").strip()
        return choice
    
    def interactive_mode(self):
        """Run the inspector in interactive mode."""
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                if not self.classes:
                    print("\n😅 This module doesn't have any classes in the main module!")
                    continue
                
                print("\n📝 Available classes in main module:")
                for i, name in enumerate(sorted(self.classes.keys()), 1):
                    print(f"  [{i}] {name}")
                
                class_name = input("\n➤ Type the class name: ").strip()
                if class_name:
                    self.inspect_class(class_name)
            
            elif choice == '2':
                if not self.all_submodules:
                    print("\n😅 This module doesn't have any submodules!")
                    continue
                
                print("\n📝 Available submodules:")
                for i, name in enumerate(sorted(self.all_submodules.keys()), 1):
                    print(f"  [{i}] {name}")
                
                submodule_name = input("\n➤ Type the submodule name: ").strip()
                if submodule_name:
                    self.inspect_submodule(submodule_name)
            
            elif choice == '3':
                if not self.all_submodules:
                    print("\n😅 This module doesn't have any submodules!")
                    continue
                
                print("\n📝 Step 1: Choose a submodule")
                for i, name in enumerate(sorted(self.all_submodules.keys()), 1):
                    classes_count = len(self.all_submodules[name]['classes'])
                    print(f"  [{i}] {name} ({classes_count} classes)")
                
                submodule_name = input("\n➤ Type the submodule name: ").strip()
                
                if submodule_name and submodule_name in self.all_submodules:
                    sub_data = self.all_submodules[submodule_name]
                    
                    if not sub_data['classes']:
                        print(f"\n😅 Submodule '{submodule_name}' doesn't have any classes!")
                        continue
                    
                    print(f"\n📝 Step 2: Choose a class from '{submodule_name}'")
                    for i, name in enumerate(sorted(sub_data['classes'].keys()), 1):
                        details = sub_data['class_details'].get(name, {})
                        methods_count = len(details.get('methods', {}))
                        props_count = len(details.get('properties', {}))
                        print(f"  [{i}] {name} ({methods_count} methods, {props_count} properties)")
                    
                    class_name = input("\n➤ Type the class name: ").strip()
                    if class_name:
                        self.inspect_submodule_class(submodule_name, class_name)
            
            elif choice == '4':
                self.analyze_structure()
            
            elif choice == '5':
                module_name = input("\n➤ Enter new module name: ").strip()
                if module_name:
                    if self.load_module(module_name):
                        self.analyze_structure()
            
            elif choice == '6':
                print("\n" + "=" * 100)
                print("👋 Thanks for exploring Python modules!")
                print("🌟 Keep learning and have fun coding!")
                print("=" * 100)
                break
            
            else:
                print("\n❌ Oops! Please pick a number between 1 and 6.")


def main():
    """Main entry point."""
    print("\n" + "=" * 100)
    print("🐍 SUPER FRIENDLY PYTHON MODULE EXPLORER")
    print("=" * 100)
    print("\n🎉 Welcome! Let's explore Python modules together!")
    print("💡 This tool helps you see what's inside any Python module.")
    print("📚 It's like opening a toy box to see all the toys inside!\n")
    
    inspector = DeepModuleInspector()
    
    while True:
        print("💬 Some popular modules to try:")
        print("   • requests (for talking to websites)")
        print("   • json (for working with data)")
        print("   • os (for working with your computer)")
        print("   • datetime (for dates and times)")
        print("   • docx (for working with Word documents)")
        print()
        
        module_name = input("📦 What module do you want to explore? ").strip()
        
        if not module_name:
            retry = input("\n⚠️  You didn't type anything! Want to try again? (yes/no): ").strip().lower()
            if retry not in ['yes', 'y']:
                print("\n👋 Okay, bye! Come back anytime!")
                return
            continue
        
        if inspector.load_module(module_name):
            inspector.analyze_structure()
            inspector.interactive_mode()
            break
        else:
            retry = input("\n🔄 Want to try a different module? (yes/no): ").strip().lower()
            if retry not in ['yes', 'y']:
                print("\n👋 Okay, bye! Come back anytime!")
                return


if __name__ == "__main__":
    main()
