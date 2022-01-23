import enum

import octoprint.plugin

from . import keypad
from . import actions

# Each mode has a seperate action
# Mode -1: Uninitialized, tentacles have no actions
# Mode 0: Printer is printing
# Mode 1: Control mode, printer is on and not printing *default
class Mode(enum.Enum):
    UNINITIALIZED = -1
    PRINTING = 0
    CONTROL = 1

    DEFAULT = 1


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
            tentacle_action.run()
        
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
                tentacle_vars[tentacle_code][mode.name] =  {
                    'action': action['action'].name,
                    'name': action['name']
                }
        return {
            'tentacles': tentacle_vars
        }


def register_tentacle_events(*args, **kwargs):
    return ['key_press', 'key_release']
