from appdirs import user_data_dir
from pathmagic import Dir
import office

appdata = Dir(user_data_dir(appname=office.__name__, appauthor="python_module_data"))
