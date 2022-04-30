import unittest

from amplitude import utils,constants


class AmplitudeUtilsTestCase(unittest.TestCase):

    def test_utils_current_milliseconds_success(self):
        cur_time = utils.current_milliseconds()
        self.assertTrue(isinstance(cur_time, int))
        self.assertTrue(cur_time > 0)

    def test_utils_truncate_object_long_string_success(self):
        obj = {"test_key": "a" * 2000}
        truncated_obj = utils.truncate(obj)
        self.assertEqual(constants.MAX_STRING_LENGTH, len(truncated_obj["test_key"]))

    def test_utils_truncate_object_exceed_max_key_limit_log_error(self):
        obj = {}
        for i in range(2000):
            obj[str(i)] = i
        with self.assertLogs(None, "ERROR") as cm:
            truncated_obj = utils.truncate(obj)
            self.assertEqual(["ERROR:amplitude:Too many properties. 1024 maximum."], cm.output)
            self.assertEqual({}, truncated_obj)

    def test_utils_truncate_object_list_input_success(self):
        large_dict = {}
        for i in range(2000):
            large_dict[str(i)] = i
        long_string = "a" * 2000
        obj = [15, 6.6, long_string, large_dict, False]
        with self.assertLogs(None, "ERROR") as cm:
            truncated_obj = utils.truncate(obj)
            self.assertEqual(["ERROR:amplitude:Too many properties. 1024 maximum."], cm.output)
            self.assertEqual(15, truncated_obj[0])
            self.assertEqual(6.6, truncated_obj[1])
            self.assertEqual(long_string[:constants.MAX_STRING_LENGTH], truncated_obj[2])
            self.assertEqual({}, truncated_obj[3])
            self.assertFalse(truncated_obj[4])


if __name__ == '__main__':
    unittest.main()
