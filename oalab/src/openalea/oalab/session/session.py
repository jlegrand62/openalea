# -*- coding: utf-8 -*-
# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2013 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
__revision__ = ""

__all__ = ['Session']

import warnings

from openalea.core.pkgmanager import PackageManager
from openalea.core.path import path
from openalea.core.settings import get_openalea_home_dir
from openalea.vpltk.shell.shell import get_interpreter_class

from openalea.oalab.config.main import MainConfig

class Session(object):
    """
    Manage session and instantiate all widgets.
    
    MainWindow works thanks to the session
    """
    def __init__(self):
        self._project = None
        self._is_proj = False
        self._is_script = False

        self._config = MainConfig()
        self.extension = None
        
        interpreter_class = get_interpreter_class()
        self.interpreter = interpreter_class() 
        
        self.interpreter.locals['session'] = self

        self.pm = PackageManager()
        self.pm.init(verbose=False)

    @property
    def project(self):
        """
        :return: current project if one is opened. Else return None.
        """
        return self._project
            
    def current_is_project(self):
        """
        :return: True if current document is a project
        """
        return bool(self._is_proj)

    def current_is_script(self):
        """
        :return: True if current document is a script (not a project!)
        """
        return bool(self._is_script)

    def get_project(self):
        warnings.warn('Deprecated get_project -> project')
        return self.project
    
    def load_config_file(self, filename, path=None):
        self._config.load_config_file(filename, path)
                
    config = property(fget=lambda self:self._config.config)
    
    