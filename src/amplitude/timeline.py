import threading
from amplitude import constants


class Timeline:

    def __init__(self, client):
        self.locks = {
            constants.BEFORE_PLUGIN_TYPE: threading.Lock(),
            constants.ENRICHMENT_PLUGIN_TYPE: threading.Lock(),
            constants.DESTINATION_PLUGIN_TYPE: threading.Lock()
        }
        self.plugins = {
            constants.BEFORE_PLUGIN_TYPE: [],
            constants.ENRICHMENT_PLUGIN_TYPE: [],
            constants.DESTINATION_PLUGIN_TYPE: []
        }
        self.amplitude = client

    def add(self, plugin):
        with self.locks[plugin.plugin_type]:
            self.plugins[plugin.plugin_type].append(plugin)

    def remove(self, plugin):
        for plugin_type in self.locks:
            with self.locks[plugin_type]:
                self.plugins[plugin_type] = [p for p in self.plugins[plugin_type] if p != plugin]

    def process(self, event):
        before_result = self.apply_plugins(constants.BEFORE_PLUGIN_TYPE, event)
        enrich_result = self.apply_plugins(constants.ENRICHMENT_PLUGIN_TYPE, before_result)
        self.apply_plugins(constants.DESTINATION_PLUGIN_TYPE, enrich_result)
        return enrich_result

    def apply_plugins(self, plugin_type, event):
        result = event
        with self.locks[plugin_type]:
            for plugin in self.plugins[plugin_type]:
                try:
                    if plugin.plugin_type == constants.DESTINATION_PLUGIN_TYPE:
                        plugin.execute(event)
                    else:
                        result = plugin.execute(result)
                except Exception as err:
                    self.amplitude.logger.error(err)
        return result
