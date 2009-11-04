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
"""Generic Graph Widget"""



import weakref, types
from PyQt4 import QtGui, QtCore
from openalea.core.settings import Settings

import grapheditor_baselisteners
import edgefactory


#__Application_Integration_Keys__
__AIK__ = [
    "mouseMoveEvent",
    "mouseReleaseEvent",
    "mousePressEvent",
    "mouseDoubleClickEvent",
    "keyReleaseEvent",
    "keyPressEvent",
    "contextMenuEvent"
    ]



    
#------*************************************************------#
class QtGraphViewElement(grapheditor_baselisteners.GraphElementObserverBase):
    """Base class for elements in a GraphView"""

    ####################################
    # ----Class members come first---- #
    ####################################
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    @classmethod
    def set_event_handler(cls, key, handler):
        if key in cls.__application_integration__:
            cls.__application_integration__[key]=handler


    ####################################
    # ----Instance members follow----  #
    ####################################    
    def __init__(self, observed=None, graphadapter=None):
        """Ctor"""
        grapheditor_baselisteners.GraphElementObserverBase.__init__(self, 
                                                                    observed, 
                                                                    graphadapter)

        #we bind application overloads if they exist
        #once and for all. As this happens after the
        #class is constructed, it overrides any method
        #called "name" with an application-specific method
        #to handle events.
        for name, hand in self.__application_integration__.iteritems():
            if "Event" in name and hand:
                setattr(self, name, types.MethodType(hand,self,self.__class__))

    #################################
    # IGraphViewElement realisation #
    #################################       
    def add_to_view(self, view):
        view.addItem(self)

    def remove_from_view(self, view):
        view.removeItem(self)

    def position_changed(self, *args):
        """called when the position of the widget changes"""
        point = QtCore.QPointF(args[0], args[1])
        self.setPos(point)




#------*************************************************------#
class QtGraphViewVertex(QtGraphViewElement):
    """A Vertex widget should implement this interface"""
    ####################################
    # ----Class members come first---- #
    ####################################
    __state_drawing_strategies__={}

    @classmethod
    def add_drawing_strategies(cls, d):
        cls.__state_drawing_strategies__.update(d)

    @classmethod
    def get_drawing_strategy(cls, state):
        return cls.__state_drawing_strategies__.get(state)
    
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )


    ####################################
    # ----Instance members follow----  #
    ####################################    
    def __init__(self, vertex, graphadapter):
        QtGraphViewElement.__init__(self, vertex, graphadapter)
        return

    def vertex(self):
        return self.observed()

    #####################
    # ----Qt World----  #
    #####################
    # ---> state-based painting
    def select_drawing_strategy(self, state):
        return self.get_drawing_strategy(state)

    def paint(self, painter, option, widget):
        paintEvent=None #remove this
        path=None
        firstColor=None
        secondColor=None
        gradient=None

        #try to get a strategy for this state ...
        state = self.observed().get_state()
        strategy = self.select_drawing_strategy(state)
        if(strategy):
            path = strategy.get_path(self)
            gradient=strategy.get_gradient(self)
            #the gradient is already defined, no need for colors
            if(not gradient):
                firstColor=strategy.get_first_color(self)
                secondColor=strategy.get_second_color(self)
        else: #...or fall back on defaults
            rect = self.rect()
            path = QtGui.QPainterPath()
            path.addRoundedRect(rect, 5, 5)
            firstColor = self.not_selected_color
            secondColor = self.not_modified_color

        if(not gradient):
            gradient = QtGui.QLinearGradient(0, 0, 0, 100)
            gradient.setColorAt(0.0, firstColor)
            gradient.setColorAt(0.8, secondColor)

        #PAINTING
        #painter = QtGui.QPainter(self)
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        if(strategy):
            strategy.prepaint(self, paintEvent, painter, state)
        #shadow drawing:
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(100, 100, 100, 50))
        painter.drawPath(path)
        #item drawing
        painter.setBrush(QtGui.QBrush(gradient))        
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.drawPath(path)

        if(strategy):
            strategy.postpaint(self, paintEvent, painter, state)

        #selection marker is drawn at the end
        if(self.isSelected()):
            painter.setPen(QtCore.Qt.DashLine)
            painter.setBrush(QtGui.QBrush())
            painter.drawRect(self.rect())

    # ---> other events
    def polishEvent(self):
        point = self.scenePos()
        self.observed().get_ad_hoc_dict().set_metadata('position', 
                                                       [point.x(), point.y()], False)

    def moveEvent(self, event):
        point = event.newPos()
        self.observed().get_ad_hoc_dict().set_metadata('position', 
                                                       [point.x(), point.y()], False)

    def mousePressEvent(self, event):
        graphview = self.scene().views()[0]
        if (graphview and event.buttons() & QtCore.Qt.LeftButton):
            pos = event.posF().x(), event.posF.y()
            graphview.new_edge_start(pos)
            return



#------*************************************************------#
class QtGraphViewAnnotation(QtGraphViewElement):
    """A Vertex widget should implement this interface"""

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, annotation, graphadapter):
        QtGraphViewElement.__init__(self, annotation, graphadapter)
        return

    def annotation(self):
        return self.observed()

    def set_text(self, text):
        """to change the visible text, not the model text"""
        raise NotImplementedError

    def notify(self, sender, event):
        if(event[0] == "MetaDataChanged"):
            if(event[1]=="text"):
                if(event[2]): self.set_text(event[2])

        QtGraphViewElement.notify(self, sender, event)


    # ---->controllers
    def mouseDoubleClickEvent(self, event):
        """ todo """
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setSelected(True)
        self.setFocus()
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        self.setTextCursor(cursor)

    def focusOutEvent(self, event):
        """ todo """
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, False)

        # unselect text
        cursor = self.textCursor ()
        if(cursor.hasSelection()):
            cursor.clearSelection()
            self.setTextCursor(cursor)
            
        self.observed().get_ad_hoc_dict().set_metadata('text', str(self.toPlainText()))

        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)




#------*************************************************------#
class QtGraphViewEdge(QtGraphViewElement):
    """Base class for Qt based edges."""

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, edge=None, graphadapter=None, src=None, dest=None):
        QtGraphViewElement.__init__(self, edge, graphadapter)

        self.setFlag(QtGui.QGraphicsItem.GraphicsItemFlag(
            QtGui.QGraphicsItem.ItemIsSelectable))
        
        self.src = None
        self.dst = None

        if(src)  : 
            self.initialise(src)
            self.src = weakref.ref(src)
        if(dest) : 
            self.initialise(dest)
            self.dst = weakref.ref(dest)

        self.sourcePoint = QtCore.QPointF()
        self.destPoint = QtCore.QPointF()

        self.edge_path = edgefactory.EdgeFactory()
        path = self.edge_path.get_path(self.sourcePoint, self.destPoint)
        self.setPath(path)

        self.setPen(QtGui.QPen(QtCore.Qt.black, 3,
                               QtCore.Qt.SolidLine,
                               QtCore.Qt.RoundCap,
                               QtCore.Qt.RoundJoin))

    def edge(self):
        if isinstance(self.observed, weakref):
            return self.observed()
        else:
            return self.observed
        
    def update_line_source(self, *pos):
        self.sourcePoint = QtCore.QPointF(*pos)
        self.__update_line()

    def update_line_destination(self, *pos):
        self.destPoint = QtCore.QPointF(*pos)
        self.__update_line()

    def __update_line(self):
        path = self.edge_path.get_path(self.sourcePoint, self.destPoint)
        self.setPath(path)

    def notify(self, sender, event):
        if(event[0] == "MetaDataChanged"):
            if(event[1]=="canvasPosition" or event[1]=="position"):
                    pos = event[2]
                    if(sender==self.src()): 
                        self.update_line_source(*pos)
                    elif(sender==self.dst()):
                        self.update_line_destination(*pos)
            elif(event[1]=="hide" and sender==self.dst()):
                if event[2]:
                    self.setVisible(False)
                else:
                    self.setVisible(True)

    def initialise_from_model(self):
        self.src().get_ad_hoc_dict().simulate_full_data_change()
        self.dst().get_ad_hoc_dict().simulate_full_data_change()


    def remove(self):
        view = self.scene().views()[0]
        view.observed().disconnect(self.src(), self.dst())
        

    ############
    # Qt World #
    ############
    def shape(self):
        path = self.edge_path.shape()
        if not path:
            return QtGui.QGraphicsPathItem.shape(self)
        else:
            return path

    def itemChange(self, change, value):
        """ Callback when item has been modified (move...) """

        if (change == QtGui.QGraphicsItem.ItemSelectedChange):
            if(value.toBool()):
                color = QtCore.Qt.blue
            else:
                color = QtCore.Qt.black

            self.setPen(QtGui.QPen(color, 3,
                                   QtCore.Qt.SolidLine,
                                   QtCore.Qt.RoundCap,
                                   QtCore.Qt.RoundJoin))
                
        return QtGui.QGraphicsItem.itemChange(self, change, value)



class QtGraphViewFloatingEdge( QtGraphViewEdge ):

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, srcPoint, graphadapter):
        QtGraphViewEdge.__init__(self, None, graphadapter, None, None)
        self.sourcePoint = QtCore.QPointF(*srcPoint)

    def notify(self, sender, event):
        return

    def consolidate(self, graph):
        try:
            srcVertex, dstVertex = self.get_connections()
            if(srcVertex == None or dstVertex == None):
                return
            graph.add_edge(srcVertex, dstVertex)
        except Exception, e:
            print "consolidation failed :", e
        return
        
    def get_connections(self):
        #find the vertex items that were activated
        srcVertexItem = self.scene().itemAt( self.sourcePoint )
        dstVertexItem = self.scene().itemAt( self.destPoint   )

        #if the input and the output are on the same vertex...
        if(srcVertexItem == dstVertexItem):
            raise Exception("Nonsense connection : plugging self to self.")            

        return srcVertexItem.observed(), dstVertexItem.observed()



#------*************************************************------#
class QtGraphView(QtGui.QGraphicsView, grapheditor_baselisteners.GraphListenerBase):
    """A Qt implementation of GraphListenerBase    """

    ####################################
    # ----Class members come first---- #
    ####################################
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )
    __application_integration__["mimeHandlers"]={}
    __application_integration__["pressHotkeyMap"]={}
    __application_integration__["releaseHotkeyMap"]={}

    @classmethod
    def set_mime_handler_map(cls, mapping):
        cls.__application_integration__["mimeHandlers"].update(mapping)

    @classmethod
    def set_keypress_handler_map(cls, mapping):
        cls.__application_integration__["pressHotkeyMap"] = mapping

    @classmethod
    def set_keyrelease_handler_map(cls, mapping):
        cls.__application_integration__["releaseHotkeyMap"] = mapping

    ####################################
    # ----Instance members follow----  #
    ####################################   
    def __init__(self, parent, graph):
        QtGui.QGraphicsView.__init__(self, parent)
        grapheditor_baselisteners.GraphListenerBase.__init__(self, graph)

        self.__selectAdditions=False

        scene = QtGui.QGraphicsScene(self)
        #scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.setScene(scene)

        # ---Qt Stuff---
        #self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.rebuild_scene()

    def get_scene(self):
        return self.scene()

    ##################
    # QtWorld-Events #
    ##################
    def wheelEvent(self, event):
        self.centerOn(QtCore.QPointF(event.pos()))
        delta = -event.delta() / 2400.0 + 1.0
        self.scale_view(delta)

    def mouseMoveEvent(self, event):
        if(self.is_creating_edge()):
            pos = self.mapToScene(event.pos())
            self.new_edge_set_destination(pos.x(), pos.y())
            return
        QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if(self.is_creating_edge()):
            self.new_edge_end()
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)

    def accept_event(self, event):
        """ Return True if event is accepted """
        for format in self.__application_integration__["mimeHandlers"].keys():
            if event.mimeData().hasFormat(format): return format
        return None

    def dragEnterEvent(self, event):
        event.setAccepted(True if self.accept_event(event) else False)
            
    def dragMoveEvent(self, event):
        format = self.accept_event(event)
        if (format):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        format = self.accept_event(event)
        handler = self.__application_integration__["mimeHandlers"].get(format)
        if(handler):
            handler(self, event)
            return

        QtGui.QGraphicsView.dropEvent(self, event)

    def keyPressEvent(self, e):
        combo = e.modifiers().__int__(), e.key()
        action = self.__application_integration__["pressHotkeyMap"].get(combo)
        if(action):
            action.press(self, event)
        else:
            QtGui.QGraphicsView.keyPressEvent(self, e)

    def keyReleaseEvent(self, e):
        combo = e.modifiers().__int__(), e.key()
        action = self.__application_integration__["releaseHotkeyMap"].get(combo)
        if(action):
            action.release(self, event)
        else:
            QtGui.QGraphicsView.keyReleaseEvent(self, e)


    #########################
    # Other utility methods #
    #########################
    def scale_view(self, factor):
        self.scale(factor, factor)

    def rebuild_scene(self):
        """ Build the scene with graphic vertex and edge"""
        self.clear_scene()
        self.observed().simulate_construction_notifications()

    def clear_scene(self):
        """ Remove all items from the scene """
        scene = QtGui.QGraphicsScene(self)
        scene.setItemIndexMethod(QtGui.QGraphicsScene.NoIndex)
        self.setScene(scene)

    def new_edge_scene_cleanup(self, graphicalEdge):
        self.scene().removeItem(graphicalEdge)

    def new_edge_scene_init(self, graphicalEdge):
        self.scene().addItem(graphicalEdge)

    def get_selected_items(self, subcall=None):
        """ """
        if(subcall):
            return [ eval("item."+subcall) for item in self.items() if item.isSelected() and
                     isinstance(item, QtGraphViewVertex)]
        else:
            return [ item for item in self.items() if item.isSelected() and 
                     isinstance(item, QtGraphViewVertex)]

    def get_selection_center(self, selection=None):
        items = None
        if selection:
            items = selection
        else:
            items = self.get_selected_items()

        l = len(items)
        if(l == 0) : return QtCore.QPointF(30,30)
        
        sx = sum((self.graph_item[i].pos().x() for i in items))
        sy = sum((self.graph_item[i].pos().y() for i in items))
        return QtCore.QPointF( float(sx)/l, float(sy)/l )

    def select_added_elements(self, val):
        self.__selectAdditions=val

    def post_addition(self, element):
        """defining virtual bases makes the program start
        but crash during execution if the method is not implemented, where
        the interface checking system could prevent the application from
        starting, with a die-early behaviour."""
        if(self.__selectAdditions):
            element.setSelected(True)
