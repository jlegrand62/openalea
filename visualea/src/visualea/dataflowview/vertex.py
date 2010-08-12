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

import weakref, sip
from PyQt4 import QtCore, QtGui, QtSvg
from openalea.visualea.graph_operator import GraphOperator
from openalea.core import observer, compositenode
from openalea.core.node import InputPort, OutputPort, AbstractPort, AbstractNode
from openalea.core.settings import Settings
from openalea.grapheditor import qtgraphview, baselisteners, qtutils
from openalea.grapheditor.qtutils import mixin_method, safeEffects
from openalea.visualea import images_rc


"""
"""


class EvalObserver( observer.AbstractListener ):
    def __init__(self, callback):
        observer.AbstractListener.__init__(self)
        self.callback = callback
    def notify(self, sender, event):
        if event[0] == "start_eval":
            self.callback(sender, event)


class ObserverOnlyGraphicalVertex(qtgraphview.Vertex,
                                  qtutils.AleaQGraphicsRoundedRectItem,
                                  ):
    # --- PAINTING STUFF ---
    # Color Definition
    default_pen_color                = QtGui.QColor(QtCore.Qt.black)
    default_pen_selected_color       = QtGui.QColor(QtCore.Qt.white)
    default_pen_error_color          = QtGui.QColor(QtCore.Qt.red)

    default_top_color                = QtGui.QColor(200, 200, 200, 255)
    default_bottom_color             = QtGui.QColor(100, 100, 255, 255)
    default_error_color              = QtGui.QColor(255, 0, 0, 255)
    default_user_application_color   = QtGui.QColor(255, 144, 0, 200)
    default_lazy_color               = QtGui.QColor(255, 132, 148, 255) #ugly pink

    #gradient stops
    startPos = 0.0
    endPos   = 1.0

    #Shape definition
    portSpacing      = 5.0
    outMargins       = 5.0
    delayMargins     = 7.0
    evalColor        = QtGui.QColor(255, 0, 0, 200)

    default_corner_radius = 3.0
    default_margin        = 3.0
    pen_width             = 1.0

    maxTipLength = 400

    def __init__(self, vertex, graph, parent=None):
        qtutils.AleaQGraphicsRoundedRectItem.__init__(self,
                                                      self.default_corner_radius, True,
                                                      0, 0, 1, 1, parent)
        qtgraphview.Vertex.__init__(self, vertex, graph)


        # ----- The colors -----
        self.__topColor    = self.default_top_color
        self.__bottomColor = self.default_bottom_color
        self.__penColor    = self.default_pen_color

        # ----- Layout of the item -----
        self.vLayout = qtutils.VerticalLayout(margins=(self.outMargins, self.outMargins,
                                                       0., 0.),
                                              center=True)
        #  in ports
        self.inPortLayout = qtutils.HorizontalLayout(parent=self.vLayout,
                                                     innerMargins=(self.portSpacing,0.),
                                                     center=True,
                                                     mins=(5, 5))
        #  Caption
        self._caption = QtGui.QGraphicsSimpleTextItem(self)
        self.vLayout.addItem(self._caption)
        #  out ports
        self.outPortLayout = qtutils.HorizontalLayout(parent=self.vLayout,
                                                      innerMargins=(self.portSpacing,0.),
                                                      center=True,
                                                      mins=(5, 5))

        # Small dots when the vertex has hidden ports
        hiddenPortItem = HiddenPort(self)
        hiddenPortItem.setVisible(False)
        self.hiddenPortItem = hiddenPortItem
        self.inPortLayout.addFinalItem(hiddenPortItem)

        # Small box when the vertex is busy, beping evaluated
        self._busyItem = QtGui.QGraphicsRectItem(0,0,7,7, self)
        self._busyItem.setBrush(self.evalColor)
        self._busyItem.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self._busyItem.setVisible(False)

        # Clock image when the vertex has a delay
        self._delayItem = QtSvg.QGraphicsSvgItem(":icons/clock.svg",self)
        self._delayItem.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        self._delayItem.setVisible(False)

        self._delayText = QtGui.QGraphicsSimpleTextItem("0",self._delayItem)
        self._delayText.setFont(QtGui.QFont("ariana",6) )
        self._delayText.setBrush(QtGui.QBrush(QtGui.QColor(255,0,0,200) ) )
        self._delayText.setZValue(self._delayItem.zValue() + 1)
        self._delayText.setVisible(False)

        # ----- drawing nicities -----
        self.setPen(QtGui.QPen(QtCore.Qt.black, self.pen_width))
        if safeEffects:
            fx = QtGui.QGraphicsDropShadowEffect()
            fx.setOffset(2,2)
            fx.setBlurRadius(5)
            self.setGraphicsEffect(fx)

    def initialise_from_model(self):
        vertex = self.vertex()
        mdict  = vertex.get_ad_hoc_dict()

        #position/color...
        mdict.simulate_full_data_change(self, vertex)
        userColor = self.get_view_data("userColor")
        if( userColor is None ):
            self.store_view_data(useUserColor=False)

        #add connectors and configure their visibility
        for i in vertex.input_desc + vertex.output_desc:
            self.add_port(i)
        #once connectors are added we also initialise them
        for c in self.iter_connectors():
            c.initialise_from_model()

        #configure other items to be visible or not
        self.update_delay_item()
        self.update_hidden_port_item()
        self.set_graphical_tooltip(vertex.get_tip())
        self.set_graphical_caption(vertex.caption)
        #self.refresh_geometry() already done by set_graphical_caption
        self.update_colors() #last because gradient depense on geometry

    def terminate_from_model(self):
        vertex = self.vertex()
        self.remove_ports(lambda x: isinstance(x, InputPort))
        self.remove_ports(lambda x: isinstance(x, OutputPort))

    ###########
    # Queries #
    ###########
    def all_inputs_visible(self):
        for i in self.inPortLayout:
            if not i.isVisible():
                return False
        return True

    #############
    # Modifiers #
    #############
    def update_hidden_port_item (self) :
        visible = not self.all_inputs_visible() and self.isVisible()
        self.hiddenPortItem.setVisible(visible)

    def update_delay_item (self) :
        visible = self.vertex().delay > 0
        self._delayItem.setVisible(visible and self.isVisible())
        self._delayText.setVisible(visible and self.isVisible())
        if visible :
            self._delayText.setText(str(self.vertex().delay))

    def update_colors(self):
        self.__topColor    = self.default_top_color
        self.__bottomColor = self.default_bottom_color
        self.__penColor    = self.default_pen_color

        if not self.get_view_data("useUserColor"):
            if self.vertex().raise_exception:
                self.__topColor    = self.default_error_color
                self.__bottomColor = self.__topColor.darker()
                self.__penColor    = self.default_pen_error_color
            elif self.vertex().lazy:
                self.__topColor = self.default_lazy_color
                self.__bottomColor = self.__topColor.darker()
            elif self.vertex().user_application:
                self.__topColor = self.default_user_application_color
                self.__bottomColor = self.__topColor.darker()
        else:
            userColor = self.get_view_data("userColor")
            self.__topColor=QtGui.QColor(*userColor)
            self.__bottomColor=QtGui.QColor(*userColor)

        pen = self.pen()
        pen.setColor(self.__penColor)

        gradient = QtGui.QLinearGradient(self.rect().topLeft(),
                                         self.rect().bottomLeft())
        gradient.setColorAt(self.startPos, self.__topColor)
        gradient.setColorAt(self.endPos, self.__bottomColor)
        brush = QtGui.QBrush(gradient)

        self.setPen(pen)
        self.setBrush(brush)

    def set_graphical_caption(self, caption):
        """Sets the name displayed in the vertex widget, doesn't change
        the vertex data"""
        if caption == "":
            caption = " "
        if len(caption)>20 :
            caption = caption[:20]+"..."
        self._caption.setText(caption)
        self.refresh_geometry()

    def set_graphical_tooltip(self, rawtooltip):
        if rawtooltip is None:
            rawtooltip=""
        if len(rawtooltip)> self.maxTipLength:
            rawtooltip = rawtooltip[:self.maxTipLength]
            rawtooltip += "...\nSee Help tab for complete documentation"
        self.setToolTip(rawtooltip)

    ####################
    # Observer methods #
    ####################
    def store_view_data(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.vertex().get_ad_hoc_dict().set_metadata(k, v)

    def get_view_data(self, key):
        return self.vertex().get_ad_hoc_dict().get_metadata(key)

    def notify(self, sender, event):
        """ Notification sent by the vertex associated to the item """
        if event is None : return

        eventTopKey = event[0]
        if eventTopKey == "data_modified":
            key = event[1]
            if key == "caption":
                self.set_graphical_caption(event[2])
        elif eventTopKey == "internal_state_changed":
            key = event[1]
            if key == "delay":
                self.update_delay_item()
            elif key == "lazy" or key == "blocked":
                self.update_colors()
        elif(eventTopKey == "metadata_changed" and event[1]=="userColor"):
            if event[2] is None:
                self.store_view_data(useUserColor = False)
        elif eventTopKey == "exception_state_changed":
            self.update_colors()
        elif eventTopKey == "hiddenPortChange":
            self.update_hidden_port_item()
        elif(eventTopKey=="tooltip_modified"):
            self.set_graphical_tooltip(event[1])
        elif(eventTopKey == "start_eval"):
            self._busyItem.setVisible(self.isVisible())
            QtGui.QApplication.processEvents()
        elif(eventTopKey == "stop_eval"):
            self._busyItem.setVisible(False)
            QtGui.QApplication.processEvents()
        elif(eventTopKey == "input_port_added"):
            self.add_port(event[1])
        elif(eventTopKey == "output_port_added"):
            self.add_port(event[1])
        elif(eventTopKey == "cleared_input_ports"):
            self.remove_ports(lambda x: isinstance(x, InputPort))
        elif(eventTopKey == "cleared_output_ports"):
            self.remove_ports(lambda x: isinstance(x, OutputPort))
        self.update()
        qtgraphview.Vertex.notify(self, sender, event)

    #######################################
    # Methods to add/remove model ports   #
    # They automatically do the according #
    # operation in the GUI.               #
    #######################################
    def add_port(self, modelPort):
        if isinstance(modelPort, InputPort)    : l=self.inPortLayout
        elif isinstance(modelPort, OutputPort) : l=self.outPortLayout
        if modelPort not in l:
            gp = GraphicalPort(self, modelPort)
            if gp:
                l.addItem(gp)
                self.add_connector(gp)

    def remove_port(self, modelPort):
        if isinstance(modelPort, InputPort)    : l=self.inPortLayout
        elif isinstance(modelPort, OutputPort) : l=self.outPortLayout
        for gp in l:
            if gp.port() == modelPort:
                l.removeItem(gp)
                self.remove_connector(gp)

    def remove_ports(self, filter=lambda x:True):
        for con in self.connectors(filter):
            self.remove_port(con.port())

    #####################################################################
    # Code related to the layout of subitems and geometry of the vertex #
    #####################################################################
    def layout_items(self):
        geom = self.vLayout.boundingRect(force=True)
        self.vLayout.setPos(QtCore.QPointF(0.,0.))
        self._busyItem.setPos(0, 0)

        diBr = self._delayItem.boundingRect()
        dtBr = self._delayText.boundingRect()
        self._delayItem.setPos( -diBr.width()/2 - self.delayMargins,
                                (geom.height() -diBr.height())/2 )
        self._delayText.setPos( (diBr.width() -dtBr.width())/2,
                                (diBr.height()-dtBr.height())/2 )
        return geom


    def refresh_geometry(self):
        halfPortH = GraphicalPort.HEIGHT/2
        geom = self.layout_items().adjusted(-self.pen_width,
                                            halfPortH-self.pen_width,
                                            self.pen_width,
                                            -(halfPortH-self.pen_width))
        self.setRect(geom)
        self.refresh_cached_shape()

    ################
    # Drawing Code #
    ################
    def paint(self, painter, options, widget):
        path = self.shape()
        pen = self.pen()
        brush = self.brush()
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawPath(path)

        if(self.vertex().block):
            brush.setStyle(QtCore.Qt.BDiagPattern)
            painter.setBrush(brush)
            painter.drawPath(path)


    ################
    # Qt Overloads #
    ################
    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemSelectedChange:
            selected = value.toBool()
            pen = self.pen()
            brush = self.brush()
            gradient = brush.gradient()
            if selected:
                pen.setColor(self.default_pen_selected_color)
                if gradient: #invert the gradient
                    gradient.setColorAt(self.endPos, self.__topColor)
                    gradient.setColorAt(self.startPos, self.__bottomColor)
                scene = self.scene()
                scene.focusedItemChanged.emit(scene, self)
            else:
                pen.setColor(self.default_pen_color)
                if gradient: #invert the gradient
                    gradient.setColorAt(self.startPos, self.__topColor)
                    gradient.setColorAt(self.endPos, self.__bottomColor)
            self.setPen(pen)
            self.setBrush(brush)

        qtgraphview.Vertex.itemChange(self, change, value)
        return QtGui.QGraphicsRectItem.itemChange(self, change, value)


    mousePressEvent = mixin_method(qtgraphview.Vertex, QtGui.QGraphicsRectItem,
                                   "mousePressEvent")


class GraphicalVertex(ObserverOnlyGraphicalVertex):
    def __init__(self, vertex, graph, parent=None):
        ObserverOnlyGraphicalVertex.__init__(self, vertex, graph, parent)

    def mouseDoubleClickEvent(self, event):
        if event.button()==QtCore.Qt.LeftButton:
            # Read settings
            try:
                localsettings = Settings()
                str = localsettings.get("UI", "DoubleClick")
            except:
                str = "['open']"

            view = self.scene().views()[0]
            operator=GraphOperator(view, self.graph())
            operator.set_vertex_item(self)

            if('open' in str):
                operator(fName="vertex_open")()
            elif('run' in str):
                operator(fName="vertex_run")()


    def contextMenuEvent(self, event):
        """ Context menu event : Display the menu"""
        self.setSelected(True)

        operator = GraphOperator()
        operator.vertexType = GraphicalVertex
        operator.identify_focused_graph_view()
        operator.set_vertex_item(self)
        widget = operator.get_graph_view()
        menu = qtutils.AleaQMenu(widget)
        items = widget.scene().get_selected_items(GraphicalVertex)

        menu.addAction(operator("Run",             menu, "vertex_run"))
        menu.addAction(operator("Open Widget",     menu, "vertex_open"))
        if isinstance(self.vertex(), compositenode.CompositeNode):
            menu.addAction(operator("Inspect composite node", menu, "vertex_composite_inspect"))
        menu.addSeparator()
        menu.addAction(operator("Delete",          menu, "vertex_remove"))
        menu.addAction(operator("Reset",           menu, "vertex_reset"))
        menu.addAction(operator("Replace By",      menu, "vertex_replace"))
        menu.addAction(operator("Reload",          menu, "vertex_reload"))
        menu.addSeparator()
        menu.addAction(operator("Caption",         menu, "vertex_set_caption"))
        menu.addAction(operator("Show/Hide ports", menu, "vertex_show_hide_ports"))
        menu.addSeparator()

        action = operator("Mark as User Application", menu, "vertex_mark_user_app")
        action.setCheckable(True)
        action.setChecked( bool(self.vertex().user_application))
        menu.addAction(action)

        action = operator("Lazy", menu, "vertex_set_lazy")
        action.setCheckable(True)
        action.setChecked(self.vertex().lazy)
        menu.addAction(action)

        action = operator("Block", menu, "vertex_block")
        action.setCheckable(True)
        action.setChecked(self.vertex().block)
        menu.addAction(action)

        menu.addAction(operator("Internals", menu, "vertex_edit_internals"))
        menu.addSeparator()

        alignMenu = menu.addMenu("Align...")
        alignMenu.setDisabled(True)
        if len(items)>1:
            alignMenu.setDisabled(False)
            alignMenu.addAction(operator("Align horizontally", menu,  "graph_align_selection_horizontal"))
            alignMenu.addAction(operator("Align left", menu,  "graph_align_selection_left"))
            alignMenu.addAction(operator("Align right", menu,  "graph_align_selection_right"))
            alignMenu.addAction(operator("Align centered", menu,  "graph_align_selection_mean"))
            alignMenu.addAction(operator("Distribute horizontally", menu,  "graph_distribute_selection_horizontally"))
            alignMenu.addAction(operator("Distribute vertically", menu,  "graph_distribute_selection_vertically"))

        #The colouring
        colorMenu = menu.addMenu("Color...")
        colorMenu.addAction(operator("Set user color...", colorMenu, "graph_set_selection_color"))
        #check if the current selection is coloured and tick the
        #menu item if an item of the selection uses the user color.
        action = operator("Use user color", colorMenu, "graph_use_user_color")
        action.setCheckable(True)
        action.setChecked(False)
        for i in items:
            if i.vertex().get_ad_hoc_dict().get_metadata("useUserColor"):
                action.setChecked(True)
                break
        colorMenu.addAction(action)

        #display the menu...
        menu.move(event.screenPos())
        menu.show()
        event.accept()



class GraphicalInVertex(GraphicalVertex):
    def initialise_from_model(self):
        GraphicalVertex.initialise_from_model(self)
        self.polishEvent()

    def polishEvent(self):
        #fix input or output node position
        midX, top, bottom, left, right = 0.0, 0.0, 0.0, 0.0, 0.0
        first = True
        itemGeoms = self.scene().get_items(filterType=qtgraphview.Vertex,
                                           subcall= lambda x: x.boundingRect().translated(x.pos()))
        if len(itemGeoms) > 0:
            bounds = reduce(lambda x,y: x|y, itemGeoms)
        else:
            bounds = QtCore.QRectF(0,0,1,1)
        midX = bounds.center().x()
        y = bounds.top() - self.boundingRect().height()*2
        self.store_view_data(position=[midX, y])

class GraphicalOutVertex(GraphicalVertex):
    def initialise_from_model(self):
        GraphicalVertex.initialise_from_model(self)
        self.polishEvent()

    def polishEvent(self):
        #fix input or output node position
        midX, top, bottom, left, right = 0.0, 0.0, 0.0, 0.0, 0.0
        first = True
        itemGeoms = self.scene().get_items(filterType=qtgraphview.Vertex,
                                           subcall= lambda x: x.boundingRect().translated(x.pos()))
        if len(itemGeoms) > 0:
            bounds = reduce(lambda x,y: x|y, itemGeoms)
        else:
            bounds = QtCore.QRectF(0,0,1,1)
        midX = bounds.center().x()
        y = bounds.bottom()
        self.store_view_data(position=[midX, y])




#########################################################
# ----------------------- PORTS ----------------------- #
#########################################################

class HiddenPort (QtGui.QGraphicsItem):
    """Graphical representation of hidden ports"""
    __size = QtCore.QSizeF(15.,4.)
    __nosize = QtCore.QSizeF(0.0, 0.0)
    def __init__ (self, parent) :
        """"""
        QtGui.QGraphicsItem.__init__(self, parent)
        self.setToolTip("hidden ports")

    def add_to_view(self, view):
        return

    def initialise_from_model(self):
        return

    def get_id(self):
        return float("inf")

    def size(self):
        return self.__size

    def sizeHint(self, blop, blip):
        return self.size()

    def boundingRect(self):
        pos  = QtCore.QPointF(0,0)
        size = self.size()
        return QtCore.QRectF(pos, size)

    def paint(self, painter, option, widget):
        if not self.isVisible() :
            return
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(50,50,50,200) ) )
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 0) )
        for i in (0,1,2) :
            painter.drawEllipse(QtCore.QRectF(i * 5.,0.,4.,4.) )


# --------------------------- ConnectorType ---------------------------------
class GraphicalPort(QtGui.QGraphicsEllipseItem, qtgraphview.Connector):
    """ A vertex port """
    MAX_TIPLEN = 2000
    WIDTH      = 10.0
    HEIGHT     = 10.0

    def __init__(self, parent, port):
        """
        """
        QtGui.QGraphicsEllipseItem.__init__(self, 0, 0, self.WIDTH, self.HEIGHT, parent)
        qtgraphview.Connector.__init__(self, observed=port)
        self.__interfaceColor = None
        self.set_connection_modifiers(QtCore.Qt.NoModifier)
        self.initialise_from_model()

    port = baselisteners.GraphElementListenerBase.get_observed

    def initialise_from_model(self):
        port = self.port()
        mdict  = port.get_ad_hoc_dict()
        #graphical data init.
        mdict.simulate_full_data_change(self, port)
        interface = port.get_interface()
        if interface and interface.__color__ is not None:
            self.__interfaceColor = QtGui.QColor(*interface.__color__)
        #update tooltip
        self.notify(port, ("tooltip_modified", port.get_tip()))

    def change_observed(self, old, new):
        if isinstance(new, AbstractPort):
            qtgraphview.Element.clear_observed(self)
            self.set_observed(new)

    def close_and_delete(self, obj):
        self.clear_observed()
        del self

    def notify(self, sender, event):
        try :
            self.port()
        except :
            self.clear_observed()
            del self
            return

        if(event[0] in ["tooltip_modified", "stop_eval"]):
            self.__update_tooltip()
        elif(event[0]=="metadata_changed"):
            if(sender == self.port()):
                if(event[1]=="hide"):
                    if event[2]: #if hide
                        self.hide()
                    else:
                        self.show()
        qtgraphview.Connector.notify(self, sender, event)

    def clear_observed(self, *args):
        qtgraphview.Element.clear_observed(self)
        return

    def __update_tooltip(self):
        node = self.port().vertex()
        if isinstance(self.port(), OutputPort):
            data = node.get_output(self.port().get_id())
        elif isinstance(self.port(), InputPort):
            data = node.get_input(self.port().get_id())
        s = str(data)
        if(len(s) > self.MAX_TIPLEN):
            s = "String too long..."
            self.setToolTip(s)
        else:
            #self.setToolTip("Value: " + s)
            self.setToolTip(self.port().get_tip(data) )

    def get_id(self):
        return self.port().get_id()

    ##################
    # QtWorld-Events #
    #################
    def contextMenuEvent(self, event):
        if isinstance(self.port(), OutputPort):
            operator=GraphOperator()
            operator.identify_focused_graph_view()
            operator.set_port_item(self)
            menu = qtutils.AleaQMenu(operator.get_graph_view())
            menu.addAction(operator("Send to pool", menu, "port_send_to_pool"))
            menu.addAction(operator("Send to console", menu, "port_send_to_console"))
            menu.addAction(operator("Print",        menu, "port_print_value"))
            menu.show()
            menu.move(event.screenPos())
            event.accept()

    def paint(self, painter, option, widget):
        if(not self.isVisible()):
            return
        pos = self.pos()
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        gradient = QtGui.QLinearGradient(0, 0, 10, 0)
        if self.highlighted:
            gradient.setColorAt(1, QtGui.QColor(QtCore.Qt.red).light(120))
            gradient.setColorAt(0, QtGui.QColor(QtCore.Qt.darkRed).light(120))
        else:
            if self.__interfaceColor is None:
                gradient.setColorAt(0.8, QtGui.QColor(QtCore.Qt.yellow).light(120))
                gradient.setColorAt(0.2, QtGui.QColor(QtCore.Qt.darkYellow).light(120))
            else:
                gradient.setColorAt(0.8, self.__interfaceColor.light(120))
                gradient.setColorAt(0.2, self.__interfaceColor.light(120))

        painter.setBrush(QtGui.QBrush(gradient))
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 0))
        painter.drawEllipse(QtCore.QRectF(0, 0, self.WIDTH, self.HEIGHT) )


    itemChange = mixin_method(qtgraphview.Connector, QtGui.QGraphicsItem,
                              "itemChange")

