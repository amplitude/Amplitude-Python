import copy
import logging
import threading

from amplitude.constants import PluginType
from amplitude.exception import InvalidEventError
from amplitude.constants import LOGGER_NAME


class Timeline:

    def __init__(self, configuration=None):
        self.locks = {
            PluginType.BEFORE: threading.Lock(),
            PluginType.ENRICHMENT: threading.Lock(),
            PluginType.DESTINATION: threading.Lock()
        }
        self.plugins = {
            PluginType.BEFORE: [],
            PluginType.ENRICHMENT: [],
            PluginType.DESTINATION: []
        }
        self.configuration = configuration

    @property
    def logger(self):
        if self.configuration:
            return self.configuration.logger
        return logging.getLogger(LOGGER_NAME)

    def setup(self, client):
        self.configuration = client.configuration

    def add(self, plugin):
        with self.locks[plugin.plugin_type]:
            self.plugins[plugin.plugin_type].append(plugin)

    def remove(self, plugin):
        for plugin_type in self.locks:
            with self.locks[plugin_type]:
                self.plugins[plugin_type] = [p for p in self.plugins[plugin_type] if p != plugin]

    def flush(self):
        destination_futures = []
        for destination in self.plugins[PluginType.DESTINATION]:
            try:
                destination_futures.append(destination.flush())
            except Exception:
                self.logger.exception("Error for flush events")
        return destination_futures

    def process(self, event):
        if self.configuration.opt_out:
            self.logger.info("Skipped event for opt out config")
            return event
        before_result = self.apply_plugins(PluginType.BEFORE, event)
        enrich_result = self.apply_plugins(PluginType.ENRICHMENT, before_result)
        self.apply_plugins(PluginType.DESTINATION, enrich_result)
        return enrich_result

    def apply_plugins(self, plugin_type, event):
        result = event
        with self.locks[plugin_type]:
            for plugin in self.plugins[plugin_type]:
                if not result:
                    break
                try:
                    if plugin.plugin_type == PluginType.DESTINATION:
                        plugin.execute(copy.deepcopy(result))
                    else:
                        result = plugin.execute(result)
                except InvalidEventError:
                    self.logger.exception(f"Invalid event body {event}")
                except Exception:
                    self.logger.exception(f"Error for apply {plugin_type.name} plugin for event {event}")
        return result

    def shutdown(self):
        for destination in self.plugins[PluginType.DESTINATION]:
            destination.shutdown()
