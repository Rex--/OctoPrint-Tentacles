# Dictionary of actions that have been defined
# Key will be the action name, value will be a class object
ACTIONS = {}

# Return all actions
def get_actions():
    return ACTIONS

# Return a single action with 'name' or None if action does not exist
def get_action(name):
    if name in ACTIONS:
        return ACTIONS[name]
    else:
        return None

# @tentacle_action(name)
#   Define an action for a tentacle to execute
def tentacle_action(name):
    def decorator_tentacle_action(action_func):
        ACTIONS[name] = action_func
        action_func.name = name
        return action_func
    return decorator_tentacle_action

# Extend BaseAction to define a new action
class BaseAction(object):
    def __init__(self, *args, **kwargs):
        pass
    
    def configure(self, *args, **kwargs):
        pass

    def run(self):
        pass

# Printer actions get the _printer object injected
class PrinterAction(BaseAction):
    def __init__(self, printer=None, *args, **kwargs):
        self._printer = printer
 
@tentacle_action('home')
class HomeAction(PrinterAction):

    def configure(self, axis=['x', 'y', 'z']):
        self._axis = axis

    def run(self):
        self._printer.home(self._axis)

@tentacle_action('jog')
class JogAction(PrinterAction):

    def configure(self, axis=None, distance=0, speed=4500, relative=True):
        self._axis = axis
        self._distance = distance
        self._speed = speed
        self._relative = relative

    def run(self):
        self._printer.jog(self._axis, speed=self._speed, relative=self._relative)
