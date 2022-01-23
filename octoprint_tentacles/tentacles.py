import enum

import octoprint.plugin

from . import actions, keypad


# Each mode has a seperate action
# Mode -1: Uninitialized, tentacles have no actions
# Mode 0: Printer is printing
# Mode 1: Control mode, printer is on and not printing *default
class Mode(int, enum.Enum):
    UNINITIALIZED = -1
    MENU = 0
    PRINTING = 1
    CONTROL = 2
    PLOTTER = 3
    MAINTENANCE = 4


class Menu:
    def __init__(self, printer, menu_start, menu_end):
        self._printer = printer
        self._start = menu_start
        self._end = menu_end
        self._selected = None
    
    def start_menu(self, mode):
        self._selected = mode
        self._display_menu()
        return Mode.MENU
    
    def change_menu(self, opt='next'):
        if opt == 'next':
            new_mode  = self._selected + 1
        elif opt == 'prev':
            new_mode = self._selected - 1
        
        if self._start <= new_mode <= self._end:
            self._selected = Mode(new_mode)
            self._display_menu()
    
    def set_menu(self):
        self._printer.commands(f"M117 > {self._selected.name.title()} <")
        return self._selected

    def _display_menu(self):
        if self._start < self._selected < self._end:
            self._printer.commands(f"M117 < {self._selected.name.title()} >")
        elif self._start == self._selected < self._end:
            self._printer.commands(f"M117 [ {self._selected.name.title()} >")
        elif self._start < self._selected == self._end:
            self._printer.commands(f"M117 < {self._selected.name.title()} ]")
        elif self._start == self._selected == self._end:
            self._printer.commands(f"M117 [ {self._selected.name.title()} ]")
        else:
            self._printer.commands(f"M117 MENU ERROR: {self._selected.name.title()}")

class Tentacles(octoprint.plugin.StartupPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self._tentacles = {}
        # {
        # <tentacle_code>: {
        #   Mode.<mode>: {
        #       'action': <actions.BaseAction>
        #        'name': 'String Description'
        #       }
        #   }
        # }
        self._mode = Mode.UNINITIALIZED     # Set mode to uninitialized (-1)

    def on_after_startup(self, *args, **kwargs):

        # Load available actions for tentacles to use (just print them out now)
        self._logger.debug('Loading actions...')
        for action in actions.ACTIONS.keys():
            self._logger.debug(f'Action: {action}')

        # This should be dynamic 
        action_init_args = dict(printer=self._printer)

        # Load saved tentacle settings from octoprint instance
        # and map actions to keycodes
        self._logger.info('Loading tentacles...')
        tentacles_settings = self._settings.get(['tentacles'])
        for tentacle_code, tentacle_config in tentacles_settings.items():
            self._logger.debug(f"Loading tentacle: {tentacle_code}")
            self._tentacles[tentacle_code] = {}
            for mode, mode_action in tentacle_config.items():
                self._logger.debug(f"Loading action: {mode_action['action']} for mode: {mode}")
                if ('action' in mode_action) and (mode_action['action'] in actions.ACTIONS) and (Mode[mode.upper()] in Mode):
                    
                    # Init action passing it all arguments for now
                    key_action = actions.ACTIONS[mode_action['action']](**action_init_args)

                    # Configure action with defined args, or use defaults if none exist
                    if 'args' in mode_action:
                        key_action.configure(**mode_action['args'])
                    else:
                        key_action.configure()

                    # Configure name if defined
                    if 'name' in mode_action:
                        action_name = mode_action['name']
                    else:
                        action_name = mode_action['action']

                    self._tentacles[tentacle_code][Mode[mode.upper()]] = {
                        'action': key_action,
                        'name': action_name
                    }
                else:
                    self._logger.warn(f"Invalid tentacle config: {mode} - {mode_action}")


        # Setup our menu to switch modes
        menu_start = Mode.CONTROL
        menu_end = Mode.MAINTENANCE
        menu_keys = {
            4: 'menu_prev',
            5: 'menu_enter',
            6: 'menu_next'
        }

        # Setup menu button for every mode
        # Overwrites any config as of now
        self._tentacles[3] = {}
        for mode in range(menu_start, menu_end+1):
            self._tentacles[3][Mode(mode)] = {'action': 'menu_start'}

        # Setup Menu keys
        for k, menu_action in menu_keys.items():
            if k not in self._tentacles:
                self._tentacles[k] = {} # Init an empty dictionary for each key we use for the menu
            self._tentacles[k][Mode.MENU] = {'action': menu_action} # and set it to an action
        
        # Init Menu object
        self._menu = Menu(self._printer, Mode.CONTROL, Mode.MAINTENANCE)

        # Configure serial port for our tentacle device
        serial_conf = self._settings.get(['serial'], merged=True)
        self._logger.info('Starting keypad listening thread...')
        self._keypad_listener = keypad.KeypadListener(serial_conf['port'], serial_conf['baud'], self._logger, self._event_bus).start()


    # Default setting are no tentacles, and serial0 (default raspi UART)
    def get_settings_defaults(self):
        return {
            'serial':
                {
                    'port': '/dev/serial0',
                    'baud': 9600
                }
        }


    def on_event(self, event, payload, *args, **kwargs):
        
        #Listen for key press events that get emitted from our KeypadListener
        # and execute the action mapped to the keycode
        if event == 'plugin_tentacle_key_press':
            keycode = payload['keycode'][0]
            self._logger.debug(f'Got keypress: {keycode}')
            try:
                tentacle_action = self._tentacles[keycode][self._mode]['action']
            except KeyError:
                self._logger.debug(f'Keycode {keycode} is not attached to an action!')
                return
            if isinstance(tentacle_action, actions.BaseAction):
                tentacle_action.run()
            else:# It's more than likely a menu action
                if tentacle_action == 'menu_start':
                    self._mode = self._menu.start_menu(self._mode)
                elif tentacle_action == 'menu_next':
                    self._menu.change_menu(opt='next')
                elif tentacle_action == 'menu_prev':
                    self._menu.change_menu(opt='prev')
                elif tentacle_action == 'menu_enter':
                    self._mode = self._menu.set_menu()

        # Change modes on printer state change
        if event == 'PrinterStateChanged':

            if payload['state_id'] == 'PRINTING':
                self._mode = Mode.PRINTING
            elif payload['state_id'] == 'OPERATIONAL':
                self._mode = Mode.CONTROL


    def get_template_vars(self):
        tentacle_vars = {}
        for tentacle_code, tentacle_config in self._tentacles.items():
            tentacle_vars[tentacle_code] = {}
            for mode, action in tentacle_config.items():
                if isinstance(action['action'], actions.BaseAction):
                    action_name = action['action'].name
                    action_desc = action['name']
                else:
                    action_name = action['action']
                    action_desc = action_name
                tentacle_vars[tentacle_code][mode.name] =  {
                    'action': action_name,
                    'name': action_desc
                }
        return {
            'tentacles': tentacle_vars
        }


def register_tentacle_events(*args, **kwargs):
    return ['key_press', 'key_release']
