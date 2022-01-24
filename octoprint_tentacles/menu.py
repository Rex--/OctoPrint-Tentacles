import enum

from . import actions

# Each mode has a seperate action
# Mode -1: Uninitialized, tentacles have no actions
# Mode 0: Printer is printing
# Mode 1: Control mode, printer is on and not printing *default
class Mode(int, enum.Enum):
    UNINITIALIZED = -2
    PRINTING = -1
    MENU = 0        # Any mode greater than 0 will be shown in menu
    CONTROL = 1
    #PLOTTER = 2
    #MAINTENANCE = 3

    @classmethod
    def MAX(cls):
        max_mode = max(list(cls))
        return cls(max_mode)


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
