

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication,  QAction,
                             QTextEdit, QFileDialog, QMessageBox,
                             QWidget, QCheckBox, QLabel,
                             QHBoxLayout,  QVBoxLayout,
                             QComboBox, QPlainTextEdit, QLineEdit,
                             QGroupBox, QPushButton, QFileDialog,
                             QMenuBar, QAction)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.Qt import QActionGroup

sys.path.insert(0, os.path.abspath('..'))
import controllerBase
from parsers.logParser import LogParser

import os
import logging
logging.basicConfig(  # filename=os.path.basename(__file__) + ".log",
                    filemode="w",
                    format='%(asctime)-15s %(levelname)-5s :%(name)s: %(message)s',
                    level=logging.INFO)


class AppController(controllerBase.Controller):
    """
    Main and only controller
    process the user input to the parser models
    Models are passive and result returned as a method from the models
    Controller proccess the model result and present it to the user thought a widget
    """
    def __init__(self, model=None, view=None, *args, **kwargs):
        super(AppController, self).__init__(model, view)
        logging.debug("Controller created " + str(self.__repr__()))
        self._previous = None
        self._new = None

    def process(self):
        """
        Public interface
        executes de comparison of two files path on the view
        using the LogParser factory to extract the info
        """
        if self._view is None:
            logging.debug("can't process. no view associated")
            return
        if self._try_path(self._view.qw_router1.text()):
            if 'auto' != self._view.parserSelect():
                self._previous = LogParser().factory(self._view.qw_router1.text(), self._view.parserSelect() )
            else:
                self._previous = LogParser().factory(self._view.qw_router1.text())
            self._view.qw_router1.setStatus("Processed parser {}".format(self._view.parserSelect()))
            logging.info("Parsed file, object: '{}'".format(self._previous))
        else:
            self._view.qw_router1.setStatus("Can't process this path")
            logging.debug("Can't process path '{}'".format(
                self._view.qw_router1.text()))
            return

        if self._try_path(self._view.qw_router2.text()):
            if 'auto' != self._view.parserSelect():
                self._new = LogParser().factory(self._view.qw_router2.text(), self._view.parserSelect())
            else:
                self._new = LogParser().factory(self._view.qw_router2.text())
            self._view.qw_router2.setStatus("Processed parser {}".format(self._view.parserSelect()))
            logging.info("Parsed file, object: '{}'".format(self._new))
        else:
            self._view.qw_router2.setStatus("Can't process this path")
            logging.debug("Can't process path '{}'".format(
                    self._view.qw_router2.text()))
            return

        resultText = str()
        if self._view.routerIdComparison():
            resultText = ''.join([resultText, self._missing_routes()])
            resultText = ''.join([resultText, self._new_routes()])
            self.resultWindow = ShowResultWindow(parent=None)
            self.resultWindow.setText(resultText)
        else:
            self.RouterIdQuestion = RouterIdWindow(controller=self)
            self.RouterIdQuestion.populate_box1(list(self._previous.routersID()))
            self.RouterIdQuestion.populate_box2(list(self._new.routersID()))

    def process_by_keys(self, key1, key2):
        """
        If user choose the comparison to be done on different routers ID
        this process is invoked and user can select the IDs for comparison
        """
        if self._view is None:
            logging.debug("can't process. no view associated")
            return
            
        if self._previous is None:
            if self._try_path(self._view.qw_router1.text()):
                self._previous = LogParser().factory(self._view.qw_router1.text())
                self._view.qw_router1.setStatus("Processed")
                logging.info("Parsed file, object: '{}'".format(self._previous))
            else:
                self._view.qw_router1.setStatus("Can't process this path")
                logging.debug("Can't process path '{}'".format(
                    self._view.qw_router1.text()))
                return
        
        if self._new is None:
            if self._try_path(self._view.qw_router2.text()):
                self._new = LogParser().factory(self._view.qw_router2.text())
                self._view.qw_router2.setStatus("Processed")
                logging.info("Parsed file, object: '{}'".format(self._new))
            else:
                self._view.qw_router2.setStatus("Can't process this path")
                logging.debug("Can't process path '{}'".format(
                        self._view.qw_router2.text()))
                return
        
        resultText = str()
        if not self._view.routerIdComparison():
            resultText = ''.join([resultText, self._missing_routes(key1, key2)])
            resultText = ''.join([resultText, self._new_routes(key1, key2)])
            self.resultWindow = ShowResultWindow(parent=None)
            self.resultWindow.setText(resultText)
                
    def _try_path(self, path):
        """
        Try path and check if file exist
        """
        is_it_file = False
        if os.path.isfile(path):
            is_it_file = True

        return is_it_file

    def _try_utf8_path(self, path):
        """
        Returns a True if path is utf-8 enconded, or False on failure
        """
        if path.strip() == '':
            return False
        stream = open(path.strip(), mode="r", encoding="utf-8")
        try:
            stream.read()
        except UnicodeDecodeError:
            logging.debug("A decode error ocurred {}".format(stream))
            return False
        except MemoryError:
            logging.debug("A memory error ocurred {}".format(stream))
            return False
        else:
            return True

    def _compareByKey_missing(self, key1, key2):
        """
        Compare entries on files, and return the difference of the sets
        """
        if self._view.includeNexthop() and self._view.includeProtocol():
            pointer_method_previous = self._previous.routes_nexthop_protocol
            pointer_method_new = self._new.routes_nexthop_protocol
        elif self._view.includeNexthop():
            pointer_method_previous = self._previous.routes_nexthop
            pointer_method_new = self._new.routes_nexthop
        elif self._view.includeProtocol():
            pointer_method_previous = self._previous.routes_protocol
            pointer_method_new = self._new.routes_protocol
        else:
            pointer_method_previous = self._previous.routes
            pointer_method_new = self._new.routes

        previous_set = set(pointer_method_previous(key1))
        new_set = set(pointer_method_new(key2))
        result_set = previous_set - new_set
        return result_set

    def _compareByKey_new(self, key1, key2):
        """
        Compare entries on files, and return the difference of the sets
        """
        if self._view.includeNexthop() and self._view.includeProtocol():
            pointer_method_previous = self._previous.routes_nexthop_protocol
            pointer_method_new = self._new.routes_nexthop_protocol
        elif self._view.includeNexthop():
            pointer_method_previous = self._previous.routes_nexthop
            pointer_method_new = self._new.routes_nexthop
        elif self._view.includeProtocol():
            pointer_method_previous = self._previous.routes_protocol
            pointer_method_new = self._new.routes_protocol
        else:
            pointer_method_previous = self._previous.routes
            pointer_method_new = self._new.routes

        previous_set = set(pointer_method_previous(key1))
        new_set = set(pointer_method_new(key2))
        result_set = new_set - previous_set
        return result_set

    def _missing_routes(self, key1=None, key2=None):
        previous_info_keys = self._previous.routersID()
        new_info_keys = self._new.routersID()
        resultText = str()
        formatstr = self._getFormat()
        
        if (key1 is not None) and (key2 is not None):
            for item in self._compareByKey_missing(key1, key2):
                litem = list(item)
                litem.insert(0, "missing")
                litem.insert(0, key1)
                resultText = ''.join([resultText, formatstr.format(*litem)])
                resultText = ''.join([resultText, "\n"])
            return resultText
            
        for key in previous_info_keys:
            if key not in new_info_keys:
                continue
            for item in self._compareByKey_missing(key, key):
                litem = list(item)
                litem.insert(0, "missing")
                litem.insert(0, key)
                resultText = ''.join([resultText, formatstr.format(*litem)])
                resultText = ''.join([resultText, "\n"])
        return resultText

    def _new_routes(self, key1=None, key2=None):
        previous_info_keys = self._previous.routersID()
        new_info_keys = self._new.routersID()
        formatstr = self._getFormat()
        resultText = str()
        
        if (key1 is not None) and (key2 is not None):
            for item in self._compareByKey_new(key1, key2):
                litem = list(item)
                litem.insert(0, "new_route")
                litem.insert(0, key2)
                resultText = ''.join([resultText, formatstr.format(*litem)])
                resultText = ''.join([resultText, "\n"])
            return resultText
            
        for key in previous_info_keys:
            if key not in new_info_keys:
                continue
            for item in self._compareByKey_new(key, key):
                litem = list(item)
                litem.insert(0, "new_route")
                litem.insert(0, key)
                resultText = ''.join([resultText, formatstr.format(*litem)])
                resultText = ''.join([resultText, "\n"])
        return resultText

    def _getFormat(self):
        sep = self._view.separatorChar()
        charwidth = 75
        if self._view.includeNexthop() and self._view.includeProtocol():
            data_columns = 5
        elif self._view.includeNexthop() or self._view.includeProtocol():
            data_columns = 4
        else:
            data_columns = 3

        strformat = str()
        for i in range(data_columns):
            strformat += "{:<" + str(int( charwidth/data_columns )) + "}" + sep
        strformat = strformat[:len(strformat)-1]
        return strformat


class LogFileWidget(QGroupBox):
    """
    Widget used on the main view
    This widget holds the paths to the files to be compared
    """
    def __init__(self, parent=None, controller=None,  *args, **kwargs):
        super(LogFileWidget, self).__init__(parent, *args, **kwargs)
        self._parent = parent
        self.initUI()
        logging.debug("LogFileWidget created {}".format(self))

    def initUI(self):
        self.qw_file_path = QLineEdit(parent=self)
        self.qw_file_path.setToolTip("Path to the log file")
        self.qw_file_path.setFrame(False)

        self.qw_get_file = QPushButton("browse...", parent=self)
        self.qw_get_file.setToolTip("Browse for a log file")
        self.qw_get_file.setFlat(True)
        self.qw_get_file.clicked.connect(self._showDialog)

        self.status = QLabel()

        self.Hlayout = QHBoxLayout()
        self.Vlayout = QVBoxLayout()

        self.Hlayout.addWidget(self.qw_file_path)
        self.Hlayout.addWidget(self.qw_get_file)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.status)
        self.setLayout(self.Vlayout)

        self.setFlat(True)

    def text(self):
        return self.qw_file_path.text()

    def setStatus(self, text):
        self.status.setText(text)

    @pyqtSlot()
    def _showDialog(self):
        logging.debug("Button clicked: {}".format(self.qw_get_file))
        logging.debug("Parent button: {}".format(self))
        fname = QFileDialog.getOpenFileName(self, 'Set file',
                self._parent._options.getattribute("currentPath"))
        logging.debug("File selected: {}".format(fname))

        if fname[0]:
            logging.debug("File checking if utf-8: {}".format(fname[0]))
            self._parent._options.setattr("currentPath",
                                          os.path.dirname(fname[0]))
            if self._try_path(fname[0]):
                logging.debug("File is utf-8: {}".format(fname[0]))
                self.qw_file_path.setText(fname[0])
                self.status.setText("File set")
            else:
                logging.debug("File is NOT utf-8: {}".format(fname[0]))
                self.status.setText("File does not exist")

    def _try_path(self, path):
        is_it_file = False
        if os.path.isfile(path):
            is_it_file = True

        return is_it_file

    def _try_utf8(self, stream):
        "Returns a True if stream is utf-8 enconded, or False on failure"
        try:
            stream.read()
        except UnicodeDecodeError:
            logging.debug("A decode error ocurred {}".format(stream))
            return False
        except MemoryError:
            logging.debug("A memory error ocurred {}".format(stream))
            return False
        else:
            return True


class ShowResultWindow(QWidget):
    """
    Widget to present results to user
    """
    def __init__(self, parent=None, controller=None,  *args, **kwargs):
        super(ShowResultWindow, self).__init__(parent, *args, **kwargs)
        self._parent = parent
        self._controller = controller
        self.initUI()
        logging.debug("show result widget created {}".format(self))

    def initUI(self):
        self.text = QTextEdit()
        self.text.setCurrentFont(QFont("Consolas", 10))
        self.text.setReadOnly(True)
        self.save_btt = QPushButton("save as...")
        self.save_btt.clicked.connect(self._save)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.save_btt)
        self.layout.addWidget(self.text)

        self.setMinimumWidth(610)
        self.setWindowModality(Qt.ApplicationModal)
        self.setLayout(self.layout)
        self.show()

    def setText(self, text):
        self.text.setText(text)

    def getText(self):
        return self.text.toPlainText()

    @pyqtSlot()
    def _save(self):
        logging.debug("Object saving text <{}>".format(self))
        fname = QFileDialog.getSaveFileName(self, "Save File")
        if fname[0]:
            logging.debug("Saving to <{}>".format(fname[0]))
            with open(fname[0], "w", encoding="utf-8") as f:
                f.write(self.getText())


class RouterIdWindow(QWidget):
    """
    Widget to let user select keys to compare
    """
    def __init__(self, parent=None, controller=None,  *args, **kwargs):
        super(RouterIdWindow, self).__init__(parent, *args, **kwargs)
        self._parent = parent
        self._controller = controller
        self.initUI()
        logging.debug("show router Id window created {}".format(self))

    def initUI(self):
        self._group_previous = QGroupBox(parent=self)
        self._keys_previous_combobox = QComboBox(parent=self)
        self._group_new = QGroupBox(parent=self)
        self._keys_new_combobox = QComboBox(parent=self)
        
        self._group_previous.setTitle("Keys on log file 1")
        playout = QHBoxLayout()
        playout.addWidget(self._keys_previous_combobox)
        self._group_previous.setLayout(playout)
        
        self._group_new.setTitle("Keys on log file 2")
        nlayout = QHBoxLayout()
        nlayout.addWidget(self._keys_new_combobox)
        self._group_new.setLayout(nlayout)
        
        self._process_button = QPushButton("Process")
        self._process_button.clicked.connect(self._process)
        
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self._group_previous)
        self.hlayout.addWidget(self._group_new)
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.hlayout)
        self.layout.addWidget(self._process_button)
        
        self.setWindowModality(Qt.ApplicationModal)       
        self.setLayout(self.layout)
        self.show()

    def populate_box1(self, items_list):
        if isinstance(items_list, (list, tuple)):
            for item in items_list:
                self._keys_previous_combobox.addItem(str(item))
        else:
            self._keys_previous_combobox.addItem(str(items_list))
        
    def populate_box2(self, items_list):
        if isinstance(items_list, (list, tuple)):
            for item in items_list:
                self._keys_new_combobox.addItem(str(item))
        else:
            self._keys_new_combobox.addItem(str(items_list))

    def get_box1(self):
        return self._keys_previous_combobox.currentText()
        
    def get_box2(self):
        return self._keys_new_combobox.currentText()

    def _process(self):
        key1 = self.get_box1()
        key2 = self.get_box2()
        self._controller.process_by_keys(key1, key2)

class RouteTableApp(QWidget):
    """
    Main view class
    This class composes the widgets for the user to choose the logs files 
    to compare and the options for the output
    """
    def __init__(self, parent=None, controller=None,  *args, **kwargs):
        super(RouteTableApp, self).__init__(parent, *args, **kwargs)
        self._parent = parent
        self._controller = controller
        self._options = self.__Options()
        self.initUI()
        logging.debug("Main RouteTableApp created {}".format(self))

    def initUI(self):
        self.setWindowTitle("Routa Table comparison")
        logo = QIcon('img/icon/logo.png')
        self.setWindowIcon(logo)

        self.qw_router1 = LogFileWidget(parent=self)
        self.qw_router1.setTitle("Previous info")
        self.qw_router2 = LogFileWidget(parent=self)
        self.qw_router2.setTitle("New info")

        self.btn_process = QPushButton("Process")
        self.btn_process.setMaximumWidth(70)
        # self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self._process)

        self.chk_protocol = QCheckBox("include protocol?")
        self.chk_protocol.setChecked(self._options.getattribute("includeProtocolFlag"))
        self.chk_next = QCheckBox("include nexthop?")
        self.chk_next.setChecked(self._options.getattribute("includeNexthopFlag"))

        icon = QIcon('img/icon/process.svg')
        self.btn_process.setIcon(icon)

        self.menubar = QMenuBar(self)
        preferenceMenu = self.menubar.addMenu('Preferences')
        self.routerIdComparisonAction = QAction('Same Router Id', self)
        self.routerIdComparisonAction.setCheckable(True)
        self.routerIdComparisonAction.setChecked(self._options.getattribute("routerIdComparison"))
        preferenceMenu.addAction(self.routerIdComparisonAction)
        separatorMenu = preferenceMenu.addMenu("Separator")
        parserMenu = preferenceMenu.addMenu("Log type")

        # Parsers options
        self.parserAction = QActionGroup(self)
        autoAction = QAction('auto', self)
        autoAction.setCheckable(True)
        autoAction.setChecked("auto" == self._options.getattribute("parser"))
        timosAction = QAction('sros', self)
        timosAction.setCheckable(True)
        timosAction.setChecked("sros" == self._options.getattribute("parser"))
        timosBgpAction = QAction('sros bgp', self)
        timosBgpAction.setCheckable(True)
        timosBgpAction.setChecked("sros bgp" == self._options.getattribute("parser"))
        hvrpAction = QAction('hvrp', self)
        hvrpAction.setCheckable(True)
        hvrpAction.setChecked("hvrp" == self._options.getattribute("parser"))
        autoAction.triggered.connect(self._selectParser)
        timosAction.triggered.connect(self._selectParser)
        timosBgpAction.triggered.connect(self._selectParser)
        hvrpAction.triggered.connect(self._selectParser)
        self.parserAction.addAction(autoAction)
        self.parserAction.addAction(timosAction)
        self.parserAction.addAction(timosBgpAction)
        self.parserAction.addAction(hvrpAction)
        self.parserAction.setExclusive(True)
        parserMenu.addAction(autoAction)
        parserMenu.addAction(timosAction)
        parserMenu.addAction(timosBgpAction)
        parserMenu.addAction(hvrpAction)
        
        # set separators menu, mutually exclusive, and get persistent value
        self.separatorAction = QActionGroup(self)
        commaAction = QAction('comma (,)', self)
        commaAction.setCheckable(True)
        commaAction.setChecked("," in self._options.getattribute("separator"))
        semicolonAction = QAction('semicolon (;)', self)
        semicolonAction.setCheckable(True)
        semicolonAction.setChecked(";" in self._options.getattribute("separator"))
        spaceAction = QAction('space ( )', self)
        spaceAction.setCheckable(True)
        spaceAction.setChecked(" " in self._options.getattribute("separator"))
        self.separatorAction.addAction(commaAction)
        self.separatorAction.addAction(spaceAction)
        self.separatorAction.addAction(semicolonAction)
        self.separatorAction.setExclusive(True)
        commaAction.triggered.connect(self._selectSeparator)
        semicolonAction.triggered.connect(self._selectSeparator)
        spaceAction.triggered.connect(self._selectSeparator)
        separatorMenu.addAction(spaceAction)
        separatorMenu.addAction(commaAction)
        separatorMenu.addAction(semicolonAction)

        self.layout = QVBoxLayout()
        self.hlayout = QHBoxLayout()

        self.hlayout.addWidget(self.btn_process)
        self.hlayout.addWidget(self.chk_protocol)
        self.hlayout.addWidget(self.chk_next)

        self.layout.addWidget(self.menubar)
        self.layout.addWidget(self.qw_router1)
        self.layout.addWidget(self.qw_router2)
        self.layout.addLayout(self.hlayout)
        self.setLayout(self.layout)
        self.show()

    def _process(self):
        logging.debug("Button clicked {}".format(self.btn_process))
        self._controller.process()

    class __Options(object):
        """
        Hold local widget options
        """
        width = 200
        height = 100
        currentPath = ""
        compareByKey = True
        includeProtocolFlag = False
        includeNexthopFlag = False
        separator = " "
        parser = "auto"
        routerIdComparison = True

        def __init__(self):
            """
            Load default values then get the values from serialized file if any
            """
            import pickle
            try:
                with open('options.pickle', 'rb') as f:
                    self.__dict__ = pickle.load(f)
                    logging.debug("Load options widget. options {}".format(self.__dict__))
            except FileNotFoundError:
                pass

        def getattribute(self, name):
            return getattr(self, name)

        def setattr(self, name, value):
            setattr(self, name, value)
            logging.debug("Set Attr <{}> value <{}> object {}".format(name, value, self))

        def save(self):
            """
            Memento
            save class __dict__ over a persistent file
            """
            import pickle
            with open('options.pickle', 'wb') as f:
                pickle.dump(self.__dict__, f)

    def includeProtocol(self):
        return self.chk_protocol.isChecked()

    def includeNexthop(self):
        return self.chk_next.isChecked()

    def separatorChar(self):
        return self._options.separator

    def routerIdComparison(self):
        return self.routerIdComparisonAction.isChecked()

    def parserSelect(self):
        return self._options.parser
        
    def _selectSeparator(self):
        t = self.separatorAction.checkedAction().text()
        logging.debug("_selectSeparator separator <{}>".format(t))
        if ',' in t:
            self._options.setattr("separator", ',')
        elif ';' in t:
            self._options.setattr("separator", ';')
        else:
            self._options.setattr("separator", ' ')

    def _selectParser(self):
        t = self.parserAction.checkedAction().text()
        logging.debug("_selectParser parser <{}>".format(t))
        if 'auto' in t:
            self._options.setattr("parser", 'auto')
        elif 'sros' == t.strip():
            self._options.setattr("parser", 'sros')
        elif 'sros bgp' == t.strip():
            self._options.setattr("parser", 'sros bgp')
        elif 'hvrp' == t:
            self._options.setattr("parser", 'hvrp')
        else:
            self._options.setattr("parser", 'auto')
    
    def closeEvent(self, event):
        logging.debug("closing widget <{}> event <{}>".format(self, event))
        self._options.setattr("includeProtocolFlag", self.chk_protocol.isChecked())
        self._options.setattr("includeNexthopFlag", self.chk_next.isChecked())
        self._options.setattr("width", self.width())
        self._options.setattr("height", self.height())
        self._selectSeparator()
        self._selectParser()
        self._options.setattr("routerIdComparison", 
                              self.routerIdComparisonAction.isChecked())
        
        self._options.save()
        event.accept()

if __name__ == '__main__':

    mainController = AppController()
    app = QApplication(sys.argv)
    routetable_widget = RouteTableApp(controller=mainController)
    mainController.setView(routetable_widget)

    sys.exit(app.exec_())
