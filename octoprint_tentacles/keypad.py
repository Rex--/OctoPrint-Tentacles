import threading

import serial

class KeypadListener(threading.Thread):
    
    def __init__(self, port, baud, log, eventbus):
        threading.Thread.__init__(self)
        self.daemon = True
        self._port = port
        self._baud = baud
        self._logger = log
        self._event_bus = eventbus

    def run(self):
        try:
            serial_con = serial.Serial(self._port, self._baud)
        except:
            self._logger.error(f"Couldn't open serial port: {self._port}")
            return

        with serial_con as ser:
            key_buf = []
            while True:
                # Read a single byte
                key = ser.read()
                
                # Our keypad sends a byte value corresponding to a keycode
                #   followed by a delimeter ( 0xFF )
                if (key == b'\xff'):

                    # Assume the last byte stored in key_buf is a keycode
                    keycode = key_buf.pop()

                    # if the keycode is less than 128, its a key press
                    if (keycode < b'\b10000000'):
                        self._event_bus.fire('plugin_tentacle_key_press',
                                payload = { 'keycode': keycode })

                    # if the keycode is greater than 128, its a key release
                    elif (keycode > b'\b10000000'):
                        self._event_bus.fire('plugin_tentacle_key_release',
                                payload = { 'keycode': keycode })

                    # Clear the list of any remaining trash data
                    key_buf.clear()

                else:
                    # Log the data
                    key_buf.append(key)
