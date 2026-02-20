import enum
import unittest
from unittest.mock import MagicMock

from amplitude import EventOptions, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent, Revenue, RevenueEvent, \
    Plan, IngestionMetadata, constants


class AmplitudeEventTestCase(unittest.TestCase):

    def test_event_options_create_instance_with_attributes_success(self):
        event_option = EventOptions(user_id="test_user_id")
        self.assertTrue("user_id" in event_option)
        self.assertFalse("device_id" in event_option)
        self.assertEqual("test_user_id", event_option.user_id)
        self.assertEqual("test_user_id", event_option["user_id"])

    def test_base_event_create_instance_has_proper_retry_value(self):
        event = BaseEvent("test_event", user_id="test_user")
        self.assertEqual(0, event.retry)
        event.retry += 1
        self.assertEqual(1, event.retry)

    def test_base_event_set_attributes_with_wrong_key_log_error(self):
        event = BaseEvent("test_event", user_id="test_user")
        with self.assertLogs(None, "ERROR") as cm:
            event["id_device"] = "test_device_id"
            self.assertFalse("id_device" in event)
            self.assertFalse("device_id" in event)
            self.assertEqual(["ERROR:amplitude:Unexpected event property key: id_device"],
                             cm.output)

    def test_base_event_set_attributes_with_wrong_value_type_log_error(self):
        event = BaseEvent("test_event", user_id="test_user")
        with self.assertLogs(None, "ERROR") as cm:
            event["time"] = 98.6
            self.assertFalse("time" in event)
            self.assertIsNone(event["time"])
            self.assertEqual(["ERROR:amplitude:Event property time expected <class 'int'> but received <class 'float'>."],
                             cm.output)

    def test_base_event_to_json_string_success(self):
        event = BaseEvent("test_event", user_id="test_user", event_id=10)
        self.assertEqual('{"event_id": 10, "event_type": "test_event", "user_id": "test_user"}',
                         str(event))

    def test_base_event_set_plan_attribute_success(self):
        event = BaseEvent("test_event", user_id="test_user")
        event["plan"] = Plan(branch="test_branch", version_id="v1.1")
        self.assertEqual({"user_id": "test_user",
                          "event_type": "test_event",
                          "plan": {"branch": "test_branch", "versionId": "v1.1"}}, event.get_event_body())

    def test_base_event_set_ingestion_metadata_attribute_success(self):
        event = BaseEvent("test_event", user_id="test_user")
        event["ingestion_metadata"] = IngestionMetadata(source_name="test_source", source_version="test_version")
        self.assertEqual({"user_id": "test_user",
                          "event_type": "test_event",
                          "ingestion_metadata": {"source_name": "test_source", "source_version": "test_version"}}, event.get_event_body())

    def test_base_event_load_event_options_update_attributes_value(self):
        event = BaseEvent(event_type="test_event", event_properties={"properties1": "test"}, time=0)
        event_options = EventOptions(
            user_id="test_user",
            device_id="test_device",
            time=10,
            ingestion_metadata=IngestionMetadata(source_name="test_source", source_version="test_version")
        )
        event.load_event_options(event_options)
        expect_event_body = {"user_id": "test_user",
                             "device_id": "test_device",
                             "time": 10,
                             "ingestion_metadata": {"source_name": "test_source", "source_version": "test_version"},
                             "event_type": "test_event",
                             "event_properties": {"properties1": "test"}}
        self.assertEqual(expect_event_body, event.get_event_body())

    def test_callback_with_callback_function_success_callback(self):
        callback_func = MagicMock()
        test_event = BaseEvent("test_event", callback=callback_func)
        test_event.callback(200, "Test Message")
        callback_func.assert_called_once_with(test_event, 200, "Test Message")

    def test_callback_without_callback_function_success_callback(self):
        callback_func = MagicMock()
        test_event = BaseEvent("test_event", callback=None)
        test_event.callback(200, "Test Message")
        callback_func.assert_not_called()

    def test_base_event_get_event_body_success(self):
        class TestEnum(enum.Enum):
            ENUM1 = 'test'
            ENUM2 = 'test2'
        event = BaseEvent(event_type="test_event", user_id="test_user", user_properties={"email": "test@test"},
                          event_properties={'enum_properties': TestEnum.ENUM1})
        expect_dict = {"event_type": "test_event",
                       "user_id": "test_user",
                       "user_properties": {"email": "test@test"},
                       "event_properties": {"enum_properties": 'test'}}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_get_event_body_with_none_value_in_property(self):
        class TestEnum(enum.Enum):
            ENUM1 = 'test'
            ENUM2 = 'test2'
        event = BaseEvent(event_type="test_event", user_id="test_user", user_properties={"email": "test@test"},
                          event_properties={'enum_properties': TestEnum.ENUM1, 'empty_property': None})
        expect_dict = {"event_type": "test_event",
                       "user_id": "test_user",
                       "user_properties": {"email": "test@test"},
                       "event_properties": {"enum_properties": 'test'}}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_set_dict_event_attributes_with_invalid_value_failed(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        event["event_properties"] = {4: "4"}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": ["4", [5, 6]]}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": ["4", set()]}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": EventOptions()}
        self.assertFalse("event_properties" in event)

    def test_base_event_set_dict_event_attributes_with_valid_value_success(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        event["event_properties"] = {"test": ["4", {"test": True}]}
        self.assertTrue("event_properties" in event)

    def test_base_event_set_string_exceed_max_length_truncate(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        long_str = "acbdx" * 1000
        event["event_properties"] = {"test_long_str": long_str}
        expect_dict["event_properties"] = {"test_long_str": long_str[:constants.MAX_STRING_LENGTH]}
        self.assertEqual(expect_dict, event.get_event_body())
        event["device_id"] = long_str
        expect_dict["device_id"] = long_str[:constants.MAX_STRING_LENGTH]
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_set_dict_exceed_max_key_log_error(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        event["event_properties"] = {"test_max_key": {}}
        for i in range(2000):
            event["event_properties"]["test_max_key"][str(i)] = "test"
        expect_dict["event_properties"] = {"test_max_key": {}}
        with self.assertLogs(None, "ERROR") as cm:
            self.assertEqual(expect_dict, event.get_event_body())
            self.assertEqual([f'ERROR:amplitude:Too many properties. {constants.MAX_PROPERTY_KEYS} maximum.'], cm.output)

    def test_base_event_set_list_in_dict_attributes_success(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        list_properties = ["a", "c", 3, True]
        event["event_properties"] = {"list_properties": list_properties}
        expect_dict["event_properties"] = {"list_properties": list_properties}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_set_bool_in_dict_attributes_success(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        bool_properties = False
        event["event_properties"] = {"bool_properties": bool_properties}
        expect_dict["event_properties"] = {"bool_properties": bool_properties}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_set_none_in_dict_attributes_success(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        none_properties = None
        event["event_properties"] = {"none_properties": none_properties}
        expect_dict["event_properties"] = {"none_properties": none_properties}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_base_event_set_numeric_in_dict_attributes_success(self):
        event = BaseEvent(event_type="test_event", user_id="test_user")
        expect_dict = {"event_type": "test_event", "user_id": "test_user"}
        event["event_properties"] = {"float_properties": 26.92, "int_properties": 9}
        expect_dict["event_properties"] = {"float_properties": 26.92, "int_properties": 9}
        self.assertEqual(expect_dict, event.get_event_body())

    def test_identify_empty_identify_instance_not_valid(self):
        identify_obj = Identify()
        self.assertFalse(identify_obj.is_valid())

    def test_identify_set_key_success_and_valid(self):
        identify_obj = Identify()
        identify_obj.set("set_test_1", 15)
        expect_user_property = {constants.IDENTITY_OP_SET: {"set_test_1": 15}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        self.assertTrue(identify_obj.is_valid())

    def test_identify_operation_with_duplicate_key_error_log(self):
        identify_obj = Identify()
        identify_obj.set("set_test_1", 15)
        with self.assertLogs(None, "ERROR") as cm:
            identify_obj.set("set_test_1", 6)
            identify_obj.set_once("set_test_1", "test")
            self.assertEqual(['ERROR:amplitude:Key or clear all operation already set.',
                              'ERROR:amplitude:Key or clear all operation already set.'], cm.output)

    def test_identify_set_once_key_success(self):
        identify_obj = Identify()
        expect_user_property = {}
        identify_obj.set_once("set_once_test", "test")
        expect_user_property[constants.IDENTITY_OP_SET_ONCE] = {"set_once_test": "test"}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_append_key_success(self):
        identify_obj = Identify()
        identify_obj.append("append_test", ["test1", "test2"])
        expect_user_property = {constants.IDENTITY_OP_APPEND: {"append_test": ["test1", "test2"]}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_prepend_key_success(self):
        identify_obj = Identify()
        identify_obj.prepend("prepend_test", False)
        expect_user_property = {constants.IDENTITY_OP_PREPEND: {"prepend_test": False}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_pre_insert_key_success(self):
        identify_obj = Identify()
        identify_obj.pre_insert("pre_insert_test", {"dict_test": "test_value"})
        expect_user_property = {constants.IDENTITY_OP_PRE_INSERT: {"pre_insert_test": {"dict_test": "test_value"}}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_post_insert_key_success(self):
        identify_obj = Identify()
        identify_obj.post_insert("post_insert_test", 29.4)
        expect_user_property = {constants.IDENTITY_OP_POST_INSERT: {"post_insert_test": 29.4}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_remove_key_success(self):
        identify_obj = Identify()
        identify_obj.remove("remove_test", "test")
        expect_user_property = {constants.IDENTITY_OP_REMOVE: {"remove_test": "test"}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_unset_key_success(self):
        identify_obj = Identify()
        identify_obj.unset("unset_test")
        expect_user_property = {constants.IDENTITY_OP_UNSET: {"unset_test": constants.UNSET_VALUE}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_add_key_success(self):
        identify_obj = Identify()
        expect_user_property = {constants.IDENTITY_OP_ADD: {"add_test": 12}}
        identify_obj.add("add_test", 12)
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_add_key_with_wrong_type_failed(self):
        identify_obj = Identify()
        expect_user_property = {constants.IDENTITY_OP_ADD: {"add_test": "12"}}
        identify_obj.add("add_test", "12")
        self.assertNotEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_clear_all_remove_all_other_key(self):
        identify_obj = Identify()
        identify_obj.append("append_test", ["test1", "test2"])
        identify_obj.set("set_test_1", 15)
        identify_obj.add("add_test", 12)
        self.assertTrue(constants.IDENTITY_OP_ADD in identify_obj.user_properties)
        self.assertTrue(constants.IDENTITY_OP_SET in identify_obj.user_properties)
        self.assertTrue(constants.IDENTITY_OP_APPEND in identify_obj.user_properties)
        identify_obj.clear_all()
        self.assertFalse(constants.IDENTITY_OP_ADD in identify_obj.user_properties)
        self.assertFalse(constants.IDENTITY_OP_SET in identify_obj.user_properties)
        self.assertFalse(constants.IDENTITY_OP_APPEND in identify_obj.user_properties)
        expect_user_property = {constants.IDENTITY_OP_CLEAR_ALL: constants.UNSET_VALUE}
        self.assertEqual(expect_user_property, identify_obj.user_properties)

    def test_identify_event_initialization_has_proper_event_type_event_properties(self):
        expect_user_property = {constants.IDENTITY_OP_ADD: {"add_test": 12},
                                constants.IDENTITY_OP_SET: {"set_test_1": "test"}}
        identify_obj = Identify()
        identify_obj.set("set_test_1", "test")
        identify_obj.add("add_test", 12)
        event = IdentifyEvent(identify_obj=identify_obj)
        self.assertTrue(event, IdentifyEvent)
        self.assertEqual(event.event_type, constants.IDENTIFY_EVENT)
        self.assertEqual(expect_user_property, event.user_properties)

    def test_group_identify_event_initialization_has_proper_event_type_group_properties(self):
        expect_group_property = {constants.IDENTITY_OP_SET: {"set_test_1": 15},
                                 constants.IDENTITY_OP_SET_ONCE: {"set_once_test": "test"},
                                 constants.IDENTITY_OP_APPEND: {"append_test": ["test1", "test2"]},
                                 constants.IDENTITY_OP_POST_INSERT: {"post_insert_test": 29.4}}
        identify_obj = Identify()
        identify_obj.set("set_test_1", 15)
        identify_obj.set_once("set_once_test", "test")
        identify_obj.append("append_test", ["test1", "test2"])
        identify_obj.post_insert("post_insert_test", 29.4)
        event = GroupIdentifyEvent(identify_obj=identify_obj)
        self.assertEqual(expect_group_property, event.group_properties)
        self.assertEqual(constants.GROUP_IDENTIFY_EVENT, event.event_type)

    def test_revenue_price_not_float_invalid_revenue(self):
        revenue_obj = Revenue(price="30.65", quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        self.assertFalse(revenue_obj.is_valid())
        revenue_obj.price = 30.65
        self.assertTrue(revenue_obj.is_valid())

    def test_revenue_negative_or_zero_quantity_invalid_revenue(self):
        revenue_obj = Revenue(price=30.65, quantity=-2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        self.assertFalse(revenue_obj.is_valid())
        revenue_obj.quantity = 0
        self.assertFalse(revenue_obj.is_valid())
        revenue_obj.quantity = 2
        self.assertTrue(revenue_obj.is_valid())

    def test_revenue_get_event_properties_equal_to_expect_dict(self):
        expect_event_properties = {constants.REVENUE_PRICE: 30.65,
                                   constants.REVENUE_QUANTITY: 2,
                                   constants.REVENUE_PRODUCT_ID: "test_product_id",
                                   constants.REVENUE_TYPE: "test_revenue_type"}
        revenue_obj = Revenue(price=30.65, quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())

    def test_revenue_set_receipt_has_proper_receipt_and_signature(self):
        expect_event_properties = {constants.REVENUE_PRICE: 30.65,
                                   constants.REVENUE_QUANTITY: 2,
                                   constants.REVENUE_PRODUCT_ID: "test_product_id",
                                   constants.REVENUE_TYPE: "test_revenue_type",
                                   constants.REVENUE_RECEIPT: "test_receipt",
                                   constants.REVENUE_RECEIPT_SIG: "test_receipt_signature"}
        revenue_obj = Revenue(price=30.65, quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        self.assertIsNone(revenue_obj.receipt)
        self.assertIsNone(revenue_obj.receipt_sig)
        revenue_obj.set_receipt("test_receipt", "test_receipt_signature")
        self.assertEqual("test_receipt", revenue_obj.receipt)
        self.assertEqual("test_receipt_signature", revenue_obj.receipt_sig)
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())

    def test_revenue_additional_properties_equal_to_expect_dict(self):
        expect_event_properties = {constants.REVENUE_PRICE: 30.65,
                                   constants.REVENUE_QUANTITY: 2,
                                   constants.REVENUE_PRODUCT_ID: "test_product_id",
                                   constants.REVENUE_TYPE: "test_revenue_type",
                                   "other_properties": "test",
                                   "other_properties2": 2}
        properties = {"other_properties": "test", "other_properties2": 2}
        revenue_obj = Revenue(price=30.65, quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type", properties=properties)
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())

    def test_revenue_initialize_revenue_event_proper_event_attributes(self):
        expect_event_properties = {constants.REVENUE_PRICE: 30.65,
                                   constants.REVENUE_QUANTITY: 2,
                                   constants.REVENUE_PRODUCT_ID: "test_product_id",
                                   constants.REVENUE_TYPE: "test_revenue_type"}
        revenue_obj = Revenue(price=30.65, quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        event = revenue_obj.to_revenue_event()
        event2 = RevenueEvent(revenue_obj=revenue_obj)
        self.assertTrue(isinstance(event, RevenueEvent))
        self.assertEqual(event.get_event_body(), event2.get_event_body())
        self.assertEqual(constants.AMP_REVENUE_EVENT, event.event_type)
        self.assertEqual(expect_event_properties, event.event_properties)

    def test_plan_initialize_with_wrong_type_error_log_with_get_plan_body(self):
        plan = Plan(branch="branch-1", source="Python", version=5, version_id="xyz")
        expect_plan = {"branch": "branch-1", "source": "Python", "version": "5", "versionId": "xyz"}
        with self.assertLogs(None, "ERROR") as cm:
            plan_dict = plan.get_plan_body()
            self.assertTrue(isinstance(plan_dict, dict))
            self.assertFalse("version" in plan_dict)
            self.assertNotEqual(expect_plan, plan_dict)
            self.assertEqual(["ERROR:amplitude:Plan.version expected <class 'str'> but received <class 'int'>."],
                             cm.output)

    def test_plan_initialize_with_none_value_equal_to_expect_body(self):
        plan = Plan(branch="branch-1", source=None, version=None, version_id="xyz")
        expect_plan = {"branch": "branch-1", "versionId": "xyz"}
        self.assertEqual(expect_plan, plan.get_plan_body())

    def test_plan_initialize_with_all_value_equal_to_expect_body(self):
        plan = Plan(branch="branch-1", source="Python", version="5", version_id="xyz")
        expect_plan = {"branch": "branch-1", "source": "Python", "version": "5", "versionId": "xyz"}
        self.assertEqual(expect_plan, plan.get_plan_body())

    def test_event_with_plan_equal_to_expect_event_body(self):
        plan = Plan(branch="branch-1", source="Python", version="5", version_id="xyz")
        expect_plan = {"branch": "branch-1", "source": "Python", "version": "5", "versionId": "xyz"}
        event = BaseEvent("test_event", plan=plan)
        self.assertTrue("plan" in event)
        self.assertEqual({"event_type": "test_event", "plan": expect_plan}, event.get_event_body())

    def test_ingestion_metadata_initialize_with_wrong_type_error_log_with_get_body(self):
        ingestion_metadata = IngestionMetadata(source_name="test_source", source_version=1)
        expected = {"source_name": "test_source", "source_version": "1"}
        with self.assertLogs(None, "ERROR") as cm:
            ingestion_metadata_dict = ingestion_metadata.get_body()
            self.assertTrue(isinstance(ingestion_metadata_dict, dict))
            self.assertFalse("source_version" in ingestion_metadata_dict)
            self.assertNotEqual(expected, ingestion_metadata_dict)
            self.assertEqual(["ERROR:amplitude:IngestionMetadata.source_version expected <class 'str'> but received <class 'int'>."],
                             cm.output)

    def test_ingestion_metadata_initialize_with_none_value_equal_to_expect_body(self):
        ingestion_metadata = IngestionMetadata(source_name="test_source", source_version=None)
        expected = {"source_name": "test_source"}
        self.assertEqual(expected, ingestion_metadata.get_body())

    def test_ingestion_metadata_initialize_with_all_value_equal_to_expect_body(self):
        ingestion_metadata = IngestionMetadata(source_name="test_source", source_version="test_version")
        expected = {"source_name": "test_source", "source_version": "test_version"}
        self.assertEqual(expected, ingestion_metadata.get_body())

    def test_event_with_ingestion_metadata_equal_to_expect_event_body(self):
        ingestion_metadata = IngestionMetadata(source_name="test_source", source_version="test_version")
        expected = {"source_name": "test_source", "source_version": "test_version"}
        event = BaseEvent("test_event", ingestion_metadata=ingestion_metadata)
        self.assertTrue("ingestion_metadata" in event)
        self.assertEqual({"event_type": "test_event", "ingestion_metadata": expected}, event.get_event_body())

    def test_event_user_agent(self):
        expected = "test_user_agent"
        event = BaseEvent("test_event", user_agent=expected)
        self.assertTrue("user_agent" in event)
        self.assertEqual({"event_type": "test_event", "user_agent": expected}, event.get_event_body())

if __name__ == '__main__':
    unittest.main()
