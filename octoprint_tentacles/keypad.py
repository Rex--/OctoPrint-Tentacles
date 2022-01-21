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
            
        key_buf = []
        with serial_con as ser:
            while True:
                key = ser.read()
                #print(key)
                if (key == b'\xff'):
                    # Assume we have a keypress stored in key_buf
                    keycode = key_buf.pop(0)

                    # if the keycode is less than 128, its a key press
                    if (keycode < b'\b10000000'):
                        self._event_bus.fire('plugin_tentacle_key_press',
                                payload = { 'keycode': keycode })

                    # if the keycode is greater than 128, its a key release
                    elif (keycode > b'\b10000000'):
                        self._event_bus.fire('plugin_tentacle_key_release',
                                payload = { 'keycode': keycode })

                else:
                    # Log the data
                    key_buf.append(key)
