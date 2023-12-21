from ast import parse, unparse, NodeVisitor, Attribute, Name, NodeTransformer, alias, Import, ImportFrom, Call
from re import sub
from json import dump, load
from os.path import exists

class LibraryInterfaceVisitor(NodeVisitor):
    def visit_Module(self, node):
        self.d = {}
        self.generic_visit(node)      

    def visit_ClassDef(self, node):
        self.f = []
        self.generic_visit(node)
        self.d[node.name] = self.f


    def visit_FunctionDef(self, node):
        if not hasattr(self,'f'):
            self.f = []
        if node.name[0:2] != "__":
            self.f.append(node.name)

class ModuleMatchingVisitor(NodeTransformer):
    def __init__(self, request_user, module_name, mapping):
        super().__init__()
        self.request_user = request_user
        self.name = module_name
        self.imports = {}
        self.map_ = ".\\Protocols\\Mappings\\"+mapping+".json"
        if not exists(self.map_):
            with open(self.map_, 'w') as file:  
                dump({}, file, indent=4)
            self.mapping = {}
        else:
            self.mapping = load(open(self.map_))

    def visit_Module(self, node):
        self.generic_visit(node) 
        with open(self.map_, 'w') as file:  
                dump(self.mapping, file, indent=4)
        return node

    def visit_Import(self, node):
        i = Import()
        i.names = []
        for name in node.names:
            if name.name.find(self.name) != -1:
                n = "Import " + name.name
                if name.asname != None:
                    n = n + ' as ' + name.asname
                    self.imports[name.asname] = name.name
                else:
                    self.imports[name.name] = name.name
                if not self.verify_in_mapping(name.name):
                    self.ask_user(n,name.name)
                for k,v in self.mapping.items():
                    if name.name == k:
                        a = alias()
                        a.name = v
                        if name.asname != None:
                            a.asname = name.asname
                        i.names.append(a)
                        break
                    elif name.name == v:
                        a = alias()
                        a.name = k
                        if name.asname != None:
                            a.asname = name.asname
                        i.names.append(a)
                        break    
            else:
                i.names.append(name)
        self.generic_visit(node)            
        return i
    
    def visit_ImportFrom(self, node):
        i = ImportFrom()
        i.names = []
        if str(node.module).find(self.name) != -1:
            for name in node.names:
                potential_map = node.module +"."+name.name
                n = "From "+ node.module + " import " + name.name
                if name.asname != None:
                    n = n + ' as ' + name.asname
                    self.imports[name.asname] = potential_map
                else:
                    self.imports[name.name] = potential_map
                if not self.verify_in_mapping(potential_map):
                    self.ask_user(n,potential_map)
                for k,v in self.mapping.items():
                    if name.name == k:
                        a = alias()
                        a.name = v
                        if name.asname != None:
                            a.asname = name.asname
                        i.names.append(a)
                        break
                    elif name.name == v:
                        a = alias()
                        a.name = k
                        if name.asname != None:
                            a.asname = name.asname
                        i.names.append(a)
                        break    
            else:
                i.names.append(name)
        else:
            i.names =  node.names
        self.generic_visit(node) 
        return i

    def visit_Call(self, node):
        c = Call()
        if isinstance(node.func, Attribute):
            if isinstance(node.func.value, Name):
                for k, v in self.imports.items():
                    if str(node.func.value.id).find(k) != -1:
                        if not self.verify_in_mapping(v+"."+node.func.attr):
                            self.ask_user(v+"."+node.func.attr, v+"."+node.func.attr)
                        for k1,v1 in self.mapping.items():
                            if str(v+"."+node.func.attr).find(k1) != -1:
                                f = Attribute()
                                f.attr = node.func.attr
                                f.ctx = node.func.ctx
                                a = Name()
                                a.id = v1
                                a.ctx = node.func.value.ctx
                                f.value = a
                                c.func = f
                                break
                            elif str(v+"."+node.func.attr).find(v1) != -1:
                                f = Attribute()
                                a = Name()
                                a.id = k1
                                a.ctx = node.func.value.ctx
                                f.value = a
                                c.func = f
                                break
        elif isinstance(node.func, Name):
            for k, v in self.imports.items():
                if str(node.func.id).find(k) != -1:
                    if not self.verify_in_mapping(v):
                            self.ask_user(v, v)
                    for k1,v1 in self.mapping.items():
                        if v.find(k1) != -1:
                            a = Name()
                            a.id = v1
                            a.ctx = node.func.ctx
                            c.func = a
                            break
                        elif v.find(v1) != -1:
                            a = Name()
                            a.id = k1
                            a.ctx = node.func.ctx
                            c.func = a
                            break 
        c.args = node.args
        c.keywords = node.keywords
        if not hasattr(c, "func"): c.func = node.func
        self.generic_visit(node) 
        return c

    def verify_in_mapping(self, path):  
        for k,v in self.mapping.items():
            if path == k:
                return True
            elif path == v:
                return True
        return False
    
    def ask_user(self, user_txt, potential_map):
        choice = self.request_user(user_txt)
        if choice != None:
            self.mapping[potential_map] = choice

def get_library_interface(library_code):
    library_interface = {}

    for name, lines in library_code.items():
        tree = parse(lines)
        name = sub('\\\\','.',name)
        visitor = LibraryInterfaceVisitor()
        visitor.visit(tree)
        library_interface[name[:-3]] = visitor.d
    
    return library_interface

def get_module_statements_matching(module_code, module_name, mapping, request_user, path):
    tree = parse(module_code)
    visitor = ModuleMatchingVisitor(request_user, module_name, mapping)
    new_tree = visitor.visit(tree)
    transformed_code = unparse(new_tree)
    open(".\\REFACTORED\\"+sub('\\\\','_',path),"w",encoding="utf-8").write(transformed_code)