
import logging
logging.basicConfig(# filename=os.path.basename(__file__) + ".log", 
                    filemode="w",
                    format='%(asctime)-15s %(levelname)-5s :%(name)s: %(message)s',
                    level=logging.DEBUG)

class Controller(object):
    def __init__(self, model=None, view=None, *args, **kwargs):
        self._model = model
        self._view = view
        logging.debug("Controller created " + str(self.__repr__()) )
        
    def setView(self, view):
        if view == None:
            logging.warning("View not set , equals None")
        self._view = view
        logging.debug("Set View " + str(self.__repr__()) )
        
    def setModel(self, model):
        if self._model != None:
            self._model.unregister(self)
        self._model = model
        self._model.register(self)        
        logging.debug("Set Model " + str(self.__repr__()) )
        
    def __repr__(self):
        return ( "class: {class_} : {dict}".format(class_=self.__class__, dict=self.__dict__ )  )
        