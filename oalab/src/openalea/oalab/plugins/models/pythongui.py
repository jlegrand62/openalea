from openalea.oalab.plugins.applets import PluginApplet

class PythonModelGUI(PluginApplet):
    name = 'Python'

    def __call__(self):
        from openalea.oalab.gui.paradigm.python import PythonModelController
        return PythonModelController