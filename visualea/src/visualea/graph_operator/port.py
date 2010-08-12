# -*- python -*-
#
#       OpenAlea.Visualea: OpenAlea graphical user interface
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Daniel Barbeau <daniel.barbeau@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################

__license__ = "Cecill-C"
__revision__ = " $Id$ "

import base as graphOpBase
from PyQt4 import QtGui, QtCore
from openalea.grapheditor import qtgraphview


class PortOperators(graphOpBase.Base):
    """The PortOperators defines the output options of an output connector.

    An output connector can be sent to

        * the datapool,
        * the python interpreter
        * or print

    by right clicking on the output connector and selected the appropriate option, as shown on this screenshot.

    .. image:: ../_static/visualea_output_port.png
        :width: 600px
        :height: 400px
        :class: align-center

    """
    def port_print_value(self):
        """ Print the value of the connector """

        node = self.master.portItem().port().vertex()
        data = str(node.get_output(self.master.portItem().port().get_id()))
        data = data[:500]+"[...truncated]" if len(data)>500 else data
        print data


    def port_send_to_pool(self):
        """Send data from a connector to the dataflow


        This function is related to the menu that pops up when right clicking on a node.


        .. seealso:: :class:`openalea.visualea.dataflowview.vertex.GraphicalPort`

        """
        master = self.master

        (result, ok) = QtGui.QInputDialog.getText(master.get_graph_view(), "Data Pool", "Instance name",
                                                  QtGui.QLineEdit.Normal, )
        if(ok):
            from openalea.core.session import DataPool
            datapool = DataPool()  # Singleton

            port = self.master.portItem().port()
            node = port.vertex()
            data = node.get_output(port.get_id())
            datapool[str(result)] = data


    def port_send_to_console(self):
        """a portconnector to send output on a port directly to the console.


        :authors: Thomas Cokelaer, Daniel Barbeau
        """
        # get the visualea master
        master = self.master

        # pop up a widget to specify the instance name
        (result, ok) = QtGui.QInputDialog.getText(master.get_graph_view(), "Console", "Instance name",
                                                  QtGui.QLineEdit.Normal, )
        result = str(result)

        if(ok):
            port = self.master.portItem().port()
            node = port.vertex()
            data = node.get_output(port.get_id())
            shell = master.get_interpreter()

            overwrite = QtGui.QMessageBox.Ok
            if result in shell.interpreter.locals:
                overwrite = QtGui.QMessageBox.warning(master.get_graph_view(), "Overwrite variable?",
                                                      "Variable name '" + result +"' is already used in the interpreter," +\
                                                      "Do you want to overwrite it?",
                                                      QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                      QtGui.QMessageBox.Ok)
            if overwrite == QtGui.QMessageBox.Ok:
                shell.interpreter.locals[result]=data
                # print the instance name and content as if the user type its name in a shell
                # this is only to make obvious the availability of the instance in the shell.
                shell.interpreter.runsource("print '%s'\n" % result)
                shell.interpreter.runsource("%s\n" % result)

            shell.setFocus()