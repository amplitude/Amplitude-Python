from amplitude.plugin import BeforePlugin, EnrichmentPlugin, DestinationPlugin


class Timeline:

    def __init__(self):
        self.before = []
        self.enrichment = []
        self.destination = []

    def add(self, plugin):
        if isinstance(plugin, BeforePlugin):
            self.before.append(plugin)
        elif isinstance(plugin, EnrichmentPlugin):
            self.enrichment.append(plugin)
        elif isinstance(plugin, DestinationPlugin):
            self.destination.append(plugin)

    def remove(self, plugin):
        pass

    def process(self, event):
        pass
