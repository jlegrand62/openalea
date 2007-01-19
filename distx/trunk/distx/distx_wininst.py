################################################################################
# -*- python -*-
#
#       OpenAlea.DistX:  Distutils extension
#
#       Copyright or � or Copr. 2006 INRIA - CIRAD - INRA  
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
`distx_bdist_wininst` overrides standard `bdist_wininst` command.
"""

__license__= "Cecill-C"
__revision__=" $Id $ "


import os,sys
from distutils.command.bdist_wininst import bdist_wininst
from distutils.util import convert_path, change_root


class distx_bdist_wininst (bdist_wininst):
    """bdist_wininst extension for distx"""

    # Define user options
    user_options = []
    user_options.extend( bdist_wininst.user_options )
    user_options.append( ('external-prefix=',
                          None,
                          'Prefix directory to install external data.' ) )
    user_options.append( ('with-remote-config',
                          None,
                          "If set, windows installer will use openalea.config.prefix_dir"
                          " instead of fixed directory for installing external data" ) )

    boolean_options = ['with-remote-config']
    
    def initialize_options (self):
        bdist_wininst.initialize_options(self)
	self.external_prefix= None
        self.install_script= None
        self.with_remote_config= None

        name= self.distribution.metadata.get_name()
        self.post_install_name= name + '_postinstall_script.py'

        # Add post-install script in the module script
        if( os.name == 'nt' and self.distribution.has_external_data()):
           if not bool(self.distribution.scripts):
              self.distribution.scripts= [self.post_install_name]
           else:
              self.scripts.append(self.post_install_name)

        
    def finalize_options (self):
        bdist_wininst.finalize_options(self)

        # We use local openalea external prefix if no prefix specified
        if( not self.external_prefix ):
            try:
                import openalea.config
                self.external_prefix= openalea.config.prefix_dir
            except ImportError:
                print "!!ERROR :  Local OpenAlea config not found.",
                print "Use --external-prefix option instead\n"
                sys.exit(1)
    
        cmdobj= self.distribution.get_command_obj('install_external_data')
        cmdobj.external_prefix= self.external_prefix
        

    def run(self):
        if ( os.name != 'nt' ):
            print "bdist_wininst : No NT OS\n"
            return

        if self.distribution.has_external_data():
            scriptname= self.create_postinstall_script(self.install_script)
            self.install_script= scriptname


        bdist_wininst.run(self)


    def create_postinstall_script(self, initial_script):
        """
        Create an install script to move external data in the rigth directories.
        @param initial_script : name of the initial postinstall script or None
        @return the new post install script name
        """

        external_data= self.distribution.external_data
        if not external_data:
            return

        # Open file to write
        outscript= open( self.post_install_name, 'w')

        if(self.external_prefix):
           external_prefix=os.path.normpath(self.external_prefix)
        else:
           external_prefix=''
        
        # Write header
        outscript.write( base_script() )

        # Define destination directory
        outscript.write("final_prefix=r\'%s\'\n"%(os.path.normpath(external_prefix),))
        
        if( self.with_remote_config ):
            oa_config_test="""
try:
    from openalea import config
    final_prefix=os.path.normpath(config.prefix_dir)
    print \'Openalea config has been found.\'
except:
    print \'Openalea config not found.\'
"""
            outscript.write(oa_config_test)

        # Display destination prefix
        outscript.write("""if( final_prefix and final_prefix!=\'\') : print 'External data will be installed in ', final_prefix\n""")

        # Write external data installation script
    	for (dest, src) in external_data.items():

            # Normalize path
            dest= os.path.normpath(dest)
            dest_with_prefix= os.path.join(external_prefix, dest)                
            normal_install_dir= change_root(sys.prefix, dest_with_prefix)

            # Write move commands
            outscript.write('\ntry:\n')
            if(os.path.isabs(dest)):
                outscript.write("   copyalltree(r\'%s\', r\'%s\')\n"%(normal_install_dir,dest))
            else:
                outscript.write("   copyalltree(r\'%s\', os.path.join(final_prefix, r\'%s\'))\n"%(normal_install_dir,dest))
            outscript.write("   remove_tree(r\'%s\')\n"%(normal_install_dir))
            outscript.write("   os.removedirs(os.path.dirname(os.path.normpath(r\'%s\')))\n"%(normal_install_dir))
            outscript.write('except Exception, e: pass  \n\n')
           

        # Add environment variable
        if( self.distribution.set_env_var ):
            for p in self.distribution.set_env_var:
                outscript.write('add_env_var(r\'%s\')'%(p,))

        # call initial postinstall _script
        if(initial_script):
            try:
                importname= split(initial_script, '.')[0]
                outscript.write("import %s"%(importname,))
            except Exception, e:
                print '\n!! Warning !! Cannot include %s script in post install script.\n', e

        outscript.close()

        return self.post_install_name



def base_script():
    """
    Main base script.
    """
    return """
#This script has been auto-generated by DistX
        
import os
import shutil
from distutils.dir_util import remove_tree, mkpath

def copyalltree (src, dst):
    "Copy an entire directory tree 'src' to a new location 'dst'.  "

    try:
        names = os.listdir(src)
    except:
        return
        
    mkpath(dst)
    directory_created(dst)
            
    for n in names:
        src_name = os.path.normpath(os.path.join(src, n))
        dst_name = os.path.normpath(os.path.join(dst, n))

        if os.path.isdir(src_name):
            copyalltree(src_name, dst_name)

        else:
            shutil.copyfile(src_name, dst_name)
            file_created(dst_name)

def add_env_var(newvar):
    "Update any environment variable persistently by changing windows registry newvar is a string like 'var=value'"

    try:
        import _winreg 
        import os, sys
        from string import find

    except Exception, e:
        return
    

    def queryValue(qkey, qname):
        qvalue, type_id = _winreg.QueryValueEx(qkey, qname)
        return qvalue

    regpath = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    key = _winreg.OpenKey(reg, regpath, 0, _winreg.KEY_ALL_ACCESS)
        
    name, value = newvar.split('=')
    #specific treatment for PATH variable
    if name.upper() == 'PATH':
        value=os.path.normpath(value)    
        actualpath = queryValue(key, name)
	
	listpath=actualpath.split(';')                
        if(not value in listpath):
            value= actualpath + ';' + value
            print "ADD to PATH :", value
        else :
            value= actualpath
            
    if value:
        _winreg.SetValueEx(key, name, 0, _winreg.REG_EXPAND_SZ, value)
        

    _winreg.CloseKey(key)    
    _winreg.CloseKey(reg)                        

"""
