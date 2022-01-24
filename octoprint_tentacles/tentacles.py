import enum

import octoprint.plugin

from . import actions, keypad, menu



class Tentacles(octoprint.plugin.StartupPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self._tentacles = {}
        self._mode = menu.Mode.UNINITIALIZED

    def on_after_startup(self, *args, **kwargs):

        # Load available actions for tentacles to use (just print them out now)
        self._logger.debug('Loading actions...')
        for action in actions.ACTIONS.keys():
            self._logger.debug(f'Action: {action}')

        # This should be dynamic 
        action_init_args = dict(printer=self._printer, tentacles=self)

        # Load saved tentacle settings from octoprint instance
        # and map actions to keycodes
        self._logger.info('Loading tentacles...')
        tentacles_settings = self._settings.get(['tentacles'])
        menu_start_key = None
        for tentacle_code, tentacle_config in tentacles_settings.items():
            self._logger.debug(f"Loading tentacle: {tentacle_code}")
            self._tentacles[tentacle_code] = {}
            for mode, mode_action in tentacle_config.items():
                self._logger.debug(f"Loading action: {mode_action['action']} for mode: {mode}")
                if ('action' in mode_action) and (mode_action['action'] in actions.ACTIONS) and (menu.Mode[mode.upper()] in menu.Mode):
                    
                    # Find the menu_start key to make it easy to reference later
                    if mode_action['action'] == 'menu_start':
                        menu_start_key = tentacle_code

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
                        action_name = mode_action['action'].title()

                    self._tentacles[tentacle_code][menu.Mode[mode.upper()]] = {
                        'action': key_action,
                        'name': action_name
                    }
                else:
                    self._logger.warn(f"Invalid tentacle config: {mode} - {mode_action}")

        if menu_start_key is not None:
            # Setup our menu to switch modes
            menu_start = menu.Mode(menu.Mode.MENU + 1)
            menu_end = menu.Mode.MAX()

            # Setup menu button for every mode
            for mode in range(menu_start, menu_end+1):
                self._tentacles[menu_start_key][menu.Mode(mode)] = \
                    self._tentacles[menu_start_key][menu.Mode.MENU]
            
            # Clear menu_start button while in MENU mode
            del self._tentacles[menu_start_key][menu.Mode.MENU]

            # Init Menu object
            self._menu = menu.Menu(self._printer, menu_start, menu_end)
        else:
            self._logger.warn('No menu key defined! You will not be able to change modes!')
        # Configure serial port for our tentacle device
        serial_conf = self._settings.get(['serial'], merged=True)
        self._logger.info('Starting keypad listening thread...')
        self._keypad_listener = keypad.KeypadListener(serial_conf['port'], serial_conf['baud'], self._logger, self._event_bus).start()


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
            else:
                self._logger.err(f"Unknown action: {tentacle_action}")

        # Change modes on printer state change
        if event == 'PrinterStateChanged':

            if payload['state_id'] == 'PRINTING':
                self._mode = menu.Mode.PRINTING
            elif payload['state_id'] == 'OPERATIONAL':
                self._mode = menu.Mode.CONTROL

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

    # Default setting are no tentacles, and serial0 (default raspi UART)
    def get_settings_defaults(self):
        return {
            'serial':
                {
                    'port': '/dev/serial0',
                    'baud': 9600
                }
        }

def register_tentacle_events(*args, **kwargs):
    return ['key_press', 'key_release']
