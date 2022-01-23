# OctoPrint-Tentacles

Control OctoPrint with hardware devices. Each "tentacle" is linked to an action to perform.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html) manually using this URL:

    https://github.com/Rex--/OctoPrint-Tentacles/archive/master.zip


## Configuration

Configure tentacles in config.yaml:
```yaml
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
      5:
        control:
          action: home
          name: Home
        printing:
          action: home
          args:
            axis:
            - x
            - y
          name: Home (X/Y)
```