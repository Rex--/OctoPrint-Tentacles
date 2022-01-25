# OctoPrint-Tentacles

Control OctoPrint with hardware devices. Each "tentacle" is linked to an action to perform.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html) manually using this URL:

    https://github.com/Rex--/OctoPrint-Tentacles/archive/master.zip


## Configuration

Configure tentacles in config.yaml:
```yaml
plugins:
  tentacles:
    serial:
      port: /dev/ttyUSB0
    tentacles:
      1:
        control:
          action: jog
          args:
            axis:
              z: -1
            speed: 7500
          name: Bed Raise (Z-)
      3:
        menu:
          action: menu_start
      5:
        control:
          action: home
        plotter:
          action: plot_home
```

## Actions
Current implemented actions:

- jog
- jog-repeat
- home
- plot_home

**Menu Actions**
- menu_start
- menu_change
- menu_set


## Modes
Each tentacle has one action per mode. Some modes are available through the
mode menu. Some available menu modes are:
- control - The default mode to control the printer. Move X/Y/Z, Home, etc.
- plotter - This mode is for using your printer as a pen plotter. Moves bed
    down to fit pen attachment, sets Home offsets, etc.

Some modes are not available through the menu, but you can still assign actions to them:
- printing - This mode is set when printing. Turn lights on/off, pause print, temperature adjust
- uninitialized - This is when the printer is not connected. Use it to refresh connection, etc.

Utility modes are not available through the menu, and you probably shouldn't
be assigning custom actions unless you know what you are doing:
- menu - This mode implements the mode menu. You should assign some menu keys
    to navigate the mode menu.