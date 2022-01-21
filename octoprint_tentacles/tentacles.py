import octoprint.plugin

from . import keypad
from . import actions

class Tentacles(octoprint.plugin.StartupPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self._tentacles = {}

    def on_after_startup(self, *args, **kwargs):

        # Load available actions for tentacles to use (just print them out now)
        self._logger.debug('Loading actions...')
        for action in actions.ACTIONS.keys():
            self._logger.debug(f'Action: {action}')
        
        # Load saved tentacle settings from octoprint instance
        # and map actions to keycodes
        self._logger.info('Loading tentacles...')
        tentacles_settings = self._settings.get(['tentacles'])
        for key in tentacles_settings:
            self._logger.debug(f"Loading tentacle: {key}")
            if ({'key', 'action'} <= key.keys() ) and (key['action'] in actions.ACTIONS):
                self._tentacles[key['key']] = actions.ACTIONS[key['action']](self._printer)
                if 'args' in key:
                    action_args = key['args']
                else:
                    action_args = {}
                self._tentacles[key['key']].configure(**action_args)
            else:
                self._logger.warn(f"Invalid tentacle config: {key}")

        # Configure serial port for our tentacle device
        serial_conf = self._settings.get(['serial'], merged=True)
        self._logger.info('Starting keypad listening thread...')
        self._keypad_listener = keypad.KeypadListener(serial_conf['port'], serial_conf['baud'], self._logger, self._event_bus).start()


    # Default setting are no tentacles, and serial0 (default raspi UART)
    def get_settings_defaults(self):
        return {
            'tentacles': [],
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
                tentacle_action = self._tentacles[keycode]
            except KeyError:
                self._logger.info(f'Keycode {keycode} is not attached to an action!')
                return
            tentacle_action.run()
            

    def get_template_vars(self):
        return dict(tentacles=self._settings.get(['tentacles']))


def register_tentacle_events(*args, **kwargs):
    return ['key_press', 'key_release']
