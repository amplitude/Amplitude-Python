import unittest
from unittest.mock import MagicMock

from amplitude.plugin import AmplitudeDestinationPlugin, ContextPlugin, EventPlugin, DestinationPlugin
from amplitude import Amplitude, PluginType, BaseEvent, RevenueEvent, IdentifyEvent, GroupIdentifyEvent, Config


class AmplitudePluginTestCase(unittest.TestCase):

    def test_plugin_initialize_amplitude_client_setup_destination_plugin_success(self):
        destination_setup = MagicMock()
        AmplitudeDestinationPlugin.setup = destination_setup
        client = Amplitude("test_api_key")
        timeline = client._Amplitude__timeline
        destination_setup.assert_called_once_with(client)
        self.assertTrue(timeline.plugins[PluginType.DESTINATION])

    def test_plugin_initialize_amplitude_client_context_plugin_creation_success(self):
        client = Amplitude("test_api_key")
        timeline = client._Amplitude__timeline
        self.assertTrue(timeline.plugins[PluginType.BEFORE])
        context_plugin = timeline.plugins[PluginType.BEFORE][0]
        self.assertEqual(PluginType.BEFORE, context_plugin.plugin_type)
        client.shutdown()

    def test_plugin_context_plugin_execute_event_success(self):
        context_plugin = ContextPlugin()
        event = BaseEvent("test_event", user_id="test_user")
        self.assertIsNone(event.time)
        self.assertIsNone(event.insert_id)
        self.assertIsNone(event.library)
        context_plugin.execute(event)
        self.assertTrue(isinstance(event.time, int))
        self.assertTrue(isinstance(event.insert_id, str))
        self.assertTrue(isinstance(event.library, str))

    def test_plugin_event_plugin_process_event_success(self):
        plugin = EventPlugin(PluginType.BEFORE)
        event = BaseEvent("test_event", user_id="test_user")
        self.assertEqual(event, plugin.execute(event))
        self.assertEqual(event, plugin.track(event))
        event = RevenueEvent()
        self.assertEqual(event, plugin.execute(event))
        event = IdentifyEvent()
        self.assertEqual(event, plugin.execute(event))
        event = GroupIdentifyEvent()
        self.assertEqual(event, plugin.execute(event))

    def test_plugin_destination_plugin_add_remove_plugin_success(self):
        destination_plugin = DestinationPlugin()
        destination_plugin.timeline.configuration = Config()
        context_plugin = ContextPlugin()
        event = BaseEvent("test_event", user_id="test_user")
        destination_plugin.add(context_plugin)
        destination_plugin.execute(event)
        self.assertTrue(isinstance(event.time, int))
        self.assertTrue(isinstance(event.insert_id, str))
        self.assertTrue(isinstance(event.library, str))
        destination_plugin.remove(context_plugin)
        event = BaseEvent("test_event", user_id="test_user")
        destination_plugin.execute(event)
        self.assertIsNone(event.time)
        self.assertIsNone(event.insert_id)
        self.assertIsNone(event.library)


if __name__ == '__main__':
    unittest.main()
