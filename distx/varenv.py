################################################################################
# -*- python -*-
#
#       OpenAlea.DistX:   
#
#       Copyright or © or Copr. 2006 INRIA - CIRAD - INRA  
#
#       File author(s): Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#                       Christophe Pradal <christophe.prada@cirad.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
# 
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
################################################################################

__doc__="""
Environment variable functions
"""

__license__= "Cecill-C"
__revision__=" $Id$ "


import os
import sys

def set_lsb_env(name, vars):
    """
    Write a sh script in /etc/profile.d which set some environment variable
    LIBRARY_PATH is processes particulary in order to avoid overwrite
    @param name : file name string without extension
    @param vars : ['VAR1=VAL1', 'VAR2=VAL2', 'LIBRARY_PATH=SOMEPATH' ]
    """

    if(not 'posix' in os.name): return

    filename = '/etc/profile.d/'+name+'.sh'
    filehandle = open(filename, 'w')
    print "creating %s"%(filename,)
    
    filehandle.write("#This file has been generated by DistX\n\n")

    for newvar in vars:

        name, value = newvar.split('=')

        if(name == "LD_LIBRARY_PATH" and value):
            filehandle.write('if [ -z "$LD_LIBRARY_PATH" ]; then\n')
            filehandle.write('  export LD_LIBRARY_PATH=%s\n'%(value,))
            filehandle.write('else\n')
            filehandle.write('  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:%s\n'%(value,))
            filehandle.write('fi\n\n')
        
        elif(name and value):
            filehandle.write("export %s=%s\n\n"%(name, value))
            
    filehandle.close()



def set_win_env(vars):
    """
    Set Windows environment variable persistently by editing the registry
    @param vars : ['VAR1=VAL1', 'VAR2=VAL2', 'PATH=SOMEPATH' ]
    """

    if((not 'win' in sys.platform) or (sys.platform == 'cygwin')):
        return
    
    for newvar in vars:

        from string import find
          
        try:
            import _winreg 

        except ImportError, e:
            print "!!ERROR: Can not access to Windows registry."
            return

        def queryValue(qkey, qname):
            qvalue, type_id = _winreg.QueryValueEx(qkey, qname)
            return qvalue

        regpath = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
        reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        key = _winreg.OpenKey(reg, regpath, 0, _winreg.KEY_ALL_ACCESS)
        
        name, value = newvar.split('=')

        # Specific treatment for PATH variable
        if name.upper() == 'PATH':
            value= os.path.normpath(value)
            actualpath = queryValue(key, name)
            
            listpath = actualpath.split(';')                
            if not (value in listpath):
                value = actualpath + ';' + value
                print "ADD %s to PATH" % (value,)
            else :
                value = actualpath
            
        if(name and value):
            _winreg.SetValueEx(key, name, 0, _winreg.REG_EXPAND_SZ, value)

        _winreg.CloseKey(key)    
        _winreg.CloseKey(reg)


