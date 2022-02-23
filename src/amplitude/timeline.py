import logging
import threading
from typing import Optional

from amplitude import constants
from amplitude.client import Amplitude
from amplitude.plugin import PluginType
from amplitude.exception import InvalidEventError


logger = logging.getLogger(constants.LOGGER_NAME)


class Timeline:

    def __init__(self, client: Optional[Amplitude] = None):
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
        self.__amplitude_client = client

    def add(self, plugin):
        with self.locks[plugin.plugin_type]:
            self.plugins[plugin.plugin_type].append(plugin)

    def remove(self, plugin):
        for plugin_type in self.locks:
            with self.locks[plugin_type]:
                self.plugins[plugin_type] = [p for p in self.plugins[plugin_type] if p != plugin]

    def process(self, event):
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
                        plugin.execute(result)
                    else:
                        result = plugin.execute(result)
                except InvalidEventError as err:
                    logger.error(err)
                result = plugin.execute(result)
        return result
