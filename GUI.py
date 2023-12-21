import dearpygui.dearpygui as dpg
from _thread import start_new_thread
from yaml import safe_load
from json import load
from os.path import exists
from time import sleep
from Protocols import regenerate_interfaces, getInterfaces
from Util.ast_custom import get_module_statements_matching
from Util.glob_custom import get_py_from_directory

class GUI:
    def setup(self, protocols):
        # Helper Functions
        def add_Theme(self):
            with dpg.theme() as self.dummy_button_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (36,36,36), category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (36,36,36), category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (36,36,36), category=dpg.mvThemeCat_Core)

            with dpg.theme() as self.dummy_yellow_button_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (36,36,36), category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (36,36,36), category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (36,36,36), category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255,255,0), category=dpg.mvThemeCat_Core)

        def add_Primary_Window(self, protocols):
            with dpg.window(tag="Primary Window"):
                # Top Window
                with dpg.child_window(width=670, height=200, tag="top_window"):
                    # File selection
                    dpg.add_text(default_value="Please choose the directory for the project to refactor.")
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(width=500, tag="file_input_field", default_value='')
                        dpg.add_button(label="Directory Selector", callback=lambda: dpg.show_item("file_dialog_id"))
                        dpg.add_file_dialog(
                            directory_selector=True, show=False, callback=self.file_callback, tag="file_dialog_id",
                            width=500 ,height=400)
                        
                    dpg.add_spacer(height=10)
                    # Protocol Selection
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="From Protocol:")
                        dpg.add_spacer(width=220)
                        dpg.add_text(default_value="To Protocol:")
                    with dpg.group(horizontal=True):
                        dpg.add_listbox(items=protocols, width=322, tag="from_protocols")
                        dpg.add_listbox(items=protocols, width=322, tag="to_protocols")

                    dpg.add_spacer(height=10)
                    # Bottom Buttons
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=200)
                        dpg.add_button(label="Refresh Protocols", callback=self.refresh_protocols)
                        dpg.add_button(label="REFACTOR", tag="Refactor_button", callback=self.refactor_callback)
                dpg.add_spacer(height=10)

                # Bottom Window
                with dpg.child_window(width=670, height=150, tag="low_window"): 
                    # Console
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=300)
                        dpg.add_text(default_value="CONSOLE")
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(width=600, height=100, multiline=True, tag="Console", default_value='', enabled=False)
                    # Buttons    
                        with dpg.group(horizontal=False):
                            dpg.add_text(default_value="Every")
                            dpg.add_input_int(default_value=100, max_value=150, width=92, tag="Every_X_Line")
                            dpg.add_button(label="STOP!", height=30, callback=self.stop_refactor)
                            dpg.add_button(label="CLEAR", height=30, callback=self.clear_console)

        def add_Popup_window(self):
            with dpg.window(modal=True, show=False, tag="error_popup", no_title_bar=True, pos= [200,100], width=300, height=100):
                # Title
                f = dpg.add_button(label="", width=-1, tag="popup_txt")
                dpg.bind_item_theme(item=f, theme=self.dummy_button_theme)
                
                # OK Button
                dpg.add_spacer(height=25)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=100)
                    dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("error_popup", show=False))

        def add_Choice_Window(self):
            with dpg.window(modal=True, show=False, tag="choice_popup", height=370, no_title_bar=True, pos= [35,50]):
                with dpg.child_window(width=500, tag="Choice_child_window"):
                    f = dpg.add_button(label="Map the following function/module to the appropriate function/module", width=-1)
                    dpg.bind_item_theme(item=f, theme=self.dummy_button_theme)
                    
                    dpg.add_spacer(height=10)
                    f = dpg.add_button(label="FUNCTION", width=-1, tag="Initial_display")
                    dpg.bind_item_theme(item=f, theme=self.dummy_yellow_button_theme)
                    dpg.add_spacer(height=10)
                    
                    dpg.add_listbox(items=[dpg.get_value("to_protocols")], width=475, num_items=10, tag="choice")
                
                # Buttons
                    dpg.add_spacer(height=25)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=150)
                        dpg.add_button(label="Choose", width=75, callback=lambda: dpg.configure_item("choice_popup", show=False))
                        dpg.add_button(label="Cancel", width=75, callback=self.stop_refactor)

        # SETUP
        dpg.create_context()
        dpg.create_viewport(title='Auto-Refactoring for IoT', width=700, height=500, small_icon=".\\Util\\Icon.ico", large_icon=".\\Util\\Icon.ico")
        
        self.stop = False
        add_Theme(self)
        add_Primary_Window(self,protocols)
        add_Popup_window(self)
        add_Choice_Window(self)
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    # Callback Functions
    def add_to_console(self, line):
        prev = dpg.get_value("Console")
        if prev !="":
            if prev.count("\n") >= 19:
                prev = prev[:prev.rfind("\n")]
            dpg.configure_item("Console", default_value=line+"\n"+prev)
        else:
            dpg.configure_item("Console", default_value=line)

    def ask_user_choice(self, initial):
        dpg.configure_item("choice_popup", show=True)
        dpg.configure_item("Initial_display", label=initial)
        dpg.configure_item("choice", items=self.to_list)
        while(dpg.get_item_configuration("choice_popup")['show']):
            sleep(1)
        if not self.stop:
            if self.erase:
                self.to_list.remove(dpg.get_value("choice"))
            return dpg.get_value("to_protocols").split("_")[0].lower() + "." + dpg.get_value("choice")
        else:
            return None
        
    def clear_console(self, sender, app_data):
        dpg.configure_item("Console", default_value="")

    def file_callback(self, sender, app_data):
        dpg.configure_item("file_input_field", default_value=app_data['current_path'])

    def get_error_check(self):
        if dpg.get_value("file_input_field") == "":
            dpg.configure_item("popup_txt", label="Directory can not be left empty.")
            dpg.configure_item("error_popup", show=True)
            return True

        elif dpg.get_value("from_protocols") == dpg.get_value("to_protocols"):
            dpg.configure_item("popup_txt", label="Protocols must be different.")
            dpg.configure_item("error_popup", show=True)
            return True
        else:
            return False

    def get_Mapping(self):
        return str(dpg.get_value("to_protocols")) +"-"+ str(dpg.get_value("from_protocols"))
    
    def get_potential_erase(self):
        to_ = safe_load(open(".\\Protocols\\Interfaces\\"+dpg.get_value("to_protocols")+".yml", 'r'))
        from_ = safe_load(open(".\\Protocols\\Interfaces\\"+dpg.get_value("from_protocols")+".yml", 'r'))
        if len({k: v for k, v in from_.items()}) <= len({k: v for k, v in to_.items()}):
            self.erase = True
        else:
            self.erase = False



    def prepare_to_list(self):
        self.to_list = []
        with open(".\\Protocols\\Interfaces\\"+dpg.get_value("to_protocols")+".yml", 'r') as file:
            for module_, value in safe_load(file).items():
                for class_, v in value.items():
                    for item in v:
                        self.to_list.append(module_+"."+class_+"."+item)
        mapping = self.get_Mapping()
        self.get_potential_erase()
        if self.erase:
            # Remove from list if the value is mapped
            if exists(".\\Protocols\\Mappings\\"+mapping+".json"):
                for k,v in load(open(".\\Protocols\\Mappings\\"+mapping+".json")).items():
                    k = k[k.find('.')+1:]
                    v = v[v.find('.')+1:]
                    if k in self.to_list:
                        self.to_list.remove(k)
                    elif v in self.to_list: 
                        self.to_list.remove(v)

    def refactoring_Thread(self, directory):
        counter = 0
        max_counter = dpg.get_value("Every_X_Line")
        module_name = str(dpg.get_value("from_protocols")).split("_")[0].lower()
        mapping = self.get_Mapping()

        for module in get_py_from_directory(directory):
            if not self.stop:
                module_code =  open(directory+"\\"+module, encoding="utf8").read()
                if module_code.find(module_name) != -1:
                    get_module_statements_matching(module_code, module_name, mapping, self.ask_user_choice, module)
                else:
                    if counter == max_counter:
                        self.add_to_console("At "+module+" in the search")
                        counter = 0
                    else:
                        counter = counter + 1

    def refactor_callback(self, sender, app_data):
        self.stop = False
        if not self.get_error_check():
            self.prepare_to_list()
            try:
                start_new_thread(self.refactoring_Thread, (dpg.get_value("file_input_field"),))
            except:
                print ("Error: unable to start thread") 

    def refresh_protocols(self):
        regenerate_interfaces()
        p = getInterfaces()
        dpg.configure_item("from_protocols", items=p)
        dpg.configure_item("to_protocols", items=p)

    def stop_refactor(self, sender, app_data):
        dpg.configure_item("choice_popup", show=False)
        self.stop = True  