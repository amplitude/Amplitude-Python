import unittest
from unittest.mock import MagicMock

from amplitude import Config, EventPlugin, PluginType, BaseEvent
from amplitude.timeline import Timeline
from amplitude.plugin import AmplitudeDestinationPlugin


class AmplitudeTimelineTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.timeline = Timeline(Config())

    def test_timeline_add_remove_plugins_with_types_success(self):
        before = EventPlugin(PluginType.BEFORE)
        enrich = EventPlugin(PluginType.ENRICHMENT)
        destination = AmplitudeDestinationPlugin()
        self.timeline.add(before)
        self.assertEqual(before, self.timeline.plugins[PluginType.BEFORE][0])
        self.timeline.add(enrich)
        self.assertEqual(enrich, self.timeline.plugins[PluginType.ENRICHMENT][0])
        self.timeline.add(destination)
        self.assertEqual(destination, self.timeline.plugins[PluginType.DESTINATION][0])
        self.timeline.remove(before)
        self.assertFalse(self.timeline.plugins[PluginType.BEFORE])
        self.timeline.remove(enrich)
        self.assertFalse(self.timeline.plugins[PluginType.ENRICHMENT])
        self.timeline.remove(destination)
        self.assertFalse(self.timeline.plugins[PluginType.DESTINATION])

    def test_timeline_shutdown_destination_plugin_success(self):
        destination = AmplitudeDestinationPlugin()
        destination.shutdown = MagicMock()
        self.timeline.add(destination)
        self.timeline.shutdown()
        destination.shutdown.assert_called_once()

    def test_timeline_flush_destination_plugin_success(self):
        destination = AmplitudeDestinationPlugin()
        destination.flush = MagicMock()
        self.timeline.add(destination)
        self.timeline.flush()
        destination.flush.assert_called_once()

    def test_timeline_process_event_with_plugin_success(self):
        event = BaseEvent("test_event", "test_user")
        event2 = BaseEvent("test_event", "test_user", event_properties={"processed": True})
        enrich = EventPlugin(PluginType.ENRICHMENT)
        enrich.execute = MagicMock()
        enrich.execute.return_value = event2
        destination = AmplitudeDestinationPlugin()
        destination.execute = MagicMock()
        self.timeline.add(enrich)
        self.timeline.add(destination)
        self.assertEqual(event2, self.timeline.process(event))
        enrich.execute.assert_called_once_with(event)
        destination.execute.assert_called_once()

    def test_timeline_process_event_with_plugin_return_none_stop(self):
        event = BaseEvent("test_event", "test_user")
        event2 = BaseEvent("test_event", "test_user", event_properties={"processed": True})
        enrich = EventPlugin(PluginType.ENRICHMENT)
        enrich.execute = MagicMock()
        enrich.execute.return_value = event2
        enrich2 = EventPlugin(PluginType.ENRICHMENT)
        enrich2.execute = MagicMock()
        enrich2.execute.return_value = None
        destination = AmplitudeDestinationPlugin()
        destination.execute = MagicMock()
        self.timeline.add(enrich)
        self.timeline.add(enrich2)
        self.timeline.add(destination)
        self.assertIsNone(self.timeline.process(event))
        enrich.execute.assert_called_once_with(event)
        enrich2.execute.assert_called_once_with(event2)
        destination.execute.assert_not_called()

    def test_timeline_config_opt_out_skip_process_with_info_log(self):
        enrich = EventPlugin(PluginType.ENRICHMENT)
        enrich.execute = MagicMock()
        self.timeline.add(enrich)
        self.timeline.configuration.opt_out = True
        with self.assertLogs(None, "INFO") as cm:
            self.timeline.process(BaseEvent("test_event", "test_user"))
            self.assertEqual(["INFO:amplitude:Skipped event for opt out config"], cm.output)
            enrich.execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
