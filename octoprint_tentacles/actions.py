import octoprint.printer


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

    def _run(self):
        self._running = True
        self.run()
        self._running = False

# Menu actions get the Tentacles class instance injected
class MenuAction(BaseAction):
    def __init__(self, tentacles=None, *args, **kwargs):
        self._tentacles = tentacles

@tentacle_action('menu_start')
class StartMenuAction(MenuAction):
    def run(self):
        self._tentacles._mode = self._tentacles._menu.start_menu(self._tentacles._mode)

@tentacle_action('menu_change')
class ChangeMenuAction(MenuAction):
    def configure(self, opt=None, *args, **kwargs):
        self._opt = opt

    def run(self):
        self._tentacles._menu.change_menu(self._opt)

@tentacle_action('menu_set')
class SetMenuAction(MenuAction):
    def run(self):
        self._tentacles._mode = self._tentacles._menu.set_menu()


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

    def configure(self, axis=None, speed=4500, relative=True):
        self._axis = axis
        self._speed = speed
        self._relative = relative

    def run(self):
        self._printer.jog(self._axis, speed=self._speed, relative=self._relative)

@tentacle_action('jog-repeat')
class JogRepeatAction(octoprint.printer.PrinterCallback, JogAction):
    def configure(self, axis={}, speed=4500, relative=True):
        self._axis = axis
        self._speed = speed
        self._relative = relative
        self._jog = f"G0 { ' '.join([f'{x.upper()}{d}' for x, d in self._axis.items() ])} F{self._speed}"
        self._max_repeat = 5
        self._running = False

    def _run(self):
        print('Registering PrinterCallback')
        self._printer.register_callback(self)
        self._running = True
        if self._relative:
            self._printer.commands('G91')
        self._prev_log = self._jog
        self._printer.commands(self._jog)

    def stop(self):
        self._running = False
        self._printer.unregister_callback(self)
    
    def on_printer_add_log(self, log):
        if log.startswith('Recv: '):
            log = log[6:]
        if log == 'ok' and self._prev_log == self._jog:
            self._printer.commands('M400')
        elif log == 'ok' and self._prev_log == 'M400':
            if self._running:
                self._printer.commands(self._jog)
        elif log.startswith('Send: '):
            self._prev_log = log[6:]

# Plotter actions extend printer base

@tentacle_action('plot_home')
class HomePlotterAction(PrinterAction):

    def configure(self, home_axis=['x', 'y'], z=150, **kwargs):
        self._z = z
        self._home_axis = home_axis

    def run(self):
        self._printer.home(self._home_axis)
        self._printer.jog({'z':self._z}, relative=False, speed=4500)
