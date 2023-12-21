from Util.glob_custom import get_yml_from_Protocols_Interfaces as get_yml,\
                        get_subdir_from_Protocols_Libraries as get_libraries,\
                        get_py_from_Protocols_Libraries_LIBRARY as get_code

from Util.ast_custom import get_library_interface
from yaml import dump

def getInterfaces():
    return [i.replace('.yml', '') for i in get_yml()]

      
def regenerate_interfaces():
    for library in get_libraries():
        library_code = {}

        for module in get_code(library):
            with open('.\\Protocols\\Libraries\\'+library+"\\"+module, encoding="utf8") as f:
                library_code[module] =  f.read()

        dump(get_library_interface(library_code), open('.\\Protocols\\Interfaces\\'+library+".yml","w"))