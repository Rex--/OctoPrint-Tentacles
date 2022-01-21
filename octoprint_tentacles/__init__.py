import octoprint.plugin

from . import tentacles

__plugin_name__ = "Tentacles"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = tentacles.Tentacles()
__plugin_hooks__ = {
        'octoprint.events.register_custom_events': tentacles.register_tentacle_events,
        }
