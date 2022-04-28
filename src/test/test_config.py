import logging
import unittest
from amplitude import Config, constants
from amplitude.storage import InMemoryStorageProvider, InMemoryStorage


class AmplitudeConfigTestCase(unittest.TestCase):

    def test_config_initialize_with_default_value_success(self):
        config = Config()
        self.assertIsNone(config.api_key)
        self.assertEqual(constants.FLUSH_QUEUE_SIZE, config.flush_queue_size)
        self.assertEqual(constants.FLUSH_INTERVAL_MILLIS, config.flush_interval_millis)
        self.assertEqual(constants.FLUSH_MAX_RETRIES, config.flush_max_retries)
        self.assertEqual(logging.getLogger(constants.LOGGER_NAME), config.logger)
        self.assertIsNone(config.min_id_length)
        self.assertEqual(constants.DEFAULT_ZONE, config.server_zone)
        self.assertFalse(config.use_batch)
        self.assertEqual(constants.SERVER_URL[constants.DEFAULT_ZONE][constants.HTTP_V2], config.server_url)
        self.assertIsNone(config.callback)
        self.assertTrue(isinstance(config.storage_provider, InMemoryStorageProvider))
        self.assertFalse(config.opt_out)

    def test_config_none_api_key_invalid(self):
        config = Config()
        self.assertFalse(config.is_valid())

    def test_config_set_api_key_valid_success(self):
        config = Config(api_key="test_api_key")
        self.assertTrue(config.is_valid())
        config = Config()
        config.api_key = "test_api_key2"
        self.assertTrue(config.is_valid())

    def test_config_get_storage_success(self):
        config = Config()
        storage = config.get_storage()
        self.assertTrue(isinstance(storage, InMemoryStorage))

    def test_config_is_min_id_length_valid_success(self):
        config = Config()
        self.assertTrue(config.is_min_id_length_valid())
        config.min_id_length = 3
        self.assertTrue(config.is_min_id_length_valid())

    def test_config_min_id_length_wrong_value_invalid(self):
        config = Config(min_id_length=0)
        self.assertFalse(config.is_min_id_length_valid())
        self.assertFalse(config.is_valid())
        config.min_id_length = 5.4
        self.assertFalse(config.is_min_id_length_valid())
        self.assertFalse(config.is_valid())
        config.min_id_length = "5"
        self.assertFalse(config.is_min_id_length_valid())
        self.assertFalse(config.is_valid())
        config.min_id_length = -4
        self.assertFalse(config.is_min_id_length_valid())
        self.assertFalse(config.is_valid())

    def test_config_option_no_min_id_length_none(self):
        config = Config()
        self.assertIsNone(config.options)

    def test_config_option_with_valid_min_id_length_success(self):
        config = Config(min_id_length=7)
        self.assertEqual({"min_id_length": 7}, config.options)

    def test_config_server_url_with_server_zone_use_batch_success(self):
        config = Config()
        config.use_batch = False
        config.server_zone = constants.DEFAULT_ZONE
        self.assertEqual(constants.SERVER_URL[constants.DEFAULT_ZONE][constants.HTTP_V2], config.server_url)
        config.server_zone = constants.EU_ZONE
        self.assertEqual(constants.SERVER_URL[constants.EU_ZONE][constants.HTTP_V2], config.server_url)
        config.use_batch = True
        config.server_zone = constants.DEFAULT_ZONE
        self.assertEqual(constants.SERVER_URL[constants.DEFAULT_ZONE][constants.BATCH], config.server_url)
        config.server_zone = constants.EU_ZONE
        self.assertEqual(constants.SERVER_URL[constants.EU_ZONE][constants.BATCH], config.server_url)

    def test_config_customize_server_url_success(self):
        config = Config()
        url = "http://test_url"
        config.server_url = url
        config.use_batch = False
        config.server_zone = constants.DEFAULT_ZONE
        self.assertEqual(url, config.server_url)
        config.server_zone = constants.EU_ZONE
        self.assertEqual(url, config.server_url)
        config.use_batch = True
        config.server_zone = constants.DEFAULT_ZONE
        self.assertEqual(url, config.server_url)
        config.server_zone = constants.EU_ZONE
        self.assertEqual(url, config.server_url)

    def test_config_flush_queue_size_decrease_and_reset_success(self):
        config = Config(flush_queue_size=30)
        self.assertEqual(30, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(15, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(10, config.flush_queue_size)
        config._reset_flush_divider()
        self.assertEqual(30, config.flush_queue_size)

    def test_config_flush_queue_size_set_value_success(self):
        config = Config(flush_queue_size=20)
        self.assertEqual(20, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(10, config.flush_queue_size)
        config.flush_queue_size = 50
        self.assertEqual(50, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(25, config.flush_queue_size)

    def test_config_flush_queue_size_decrease_no_less_than_one(self):
        config = Config(flush_queue_size=2)
        self.assertEqual(2, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(1, config.flush_queue_size)
        config._increase_flush_divider()
        self.assertEqual(1, config.flush_queue_size)


if __name__ == '__main__':
    unittest.main()
