from glob import glob, escape

def get_yml_from_Protocols_Interfaces():
    return glob("*.yml", root_dir=escape('.\\Protocols\\Interfaces'))

def get_subdir_from_Protocols_Libraries():
    return glob('*', root_dir='.\\Protocols\\Libraries\\',  recursive = True)

def get_py_from_Protocols_Libraries_LIBRARY(LIBRARY):
    return  get_py_from_directory('.\\Protocols\\Libraries\\'+LIBRARY)

def get_py_from_directory(DIRECTORY):
    return glob("**\\*.py", root_dir=escape(DIRECTORY), recursive=True)