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
        port: /dev/ttyAMA1
    tentacles:
    - key: 1
        name: Bed Raise (Z-)
        action: jog
        args:
            axis:
                z: -1
            speed: 5000
    - key: 5
        name: Home (Enter)
        action: home
```