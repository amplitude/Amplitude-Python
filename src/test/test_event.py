import unittest
from unittest.mock import MagicMock

from amplitude import EventOptions, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent, Revenue, RevenueEvent, \
Plan, constants


class AmplitudeEventTestCase(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_create_event(self):
        event_option = EventOptions(user_id="test_user_id")
        self.assertTrue(isinstance(event_option, EventOptions))
        self.assertFalse(isinstance(event_option, BaseEvent))
        self.assertTrue("user_id" in event_option)
        self.assertFalse("device_id" in event_option)
        self.assertEqual("test_user_id", event_option.user_id)
        self.assertEqual("test_user_id", event_option["user_id"])
        self.assertEqual(0, event_option.retry)
        event_option.retry += 1
        self.assertEqual(1, event_option.retry)
        with self.assertLogs(None, "ERROR") as cm:
            event_option["id_device"] = "test_device_id"
            event_option["time"] = 98.6
            self.assertFalse("id_device" in event_option)
            self.assertFalse("time" in event_option)
            self.assertFalse("device_id" in event_option)
            self.assertIsNone(event_option["device_id"])
            self.assertIsNone(event_option["id_device"])
            self.assertIsNone(event_option["time"])
            self.assertEqual(["ERROR:amplitude.event:Unexpected event property key: id_device",
                              "ERROR:amplitude.event:Event property time value type: <class 'float'>. Expect <class 'int'>"],
                             cm.output)
        event_option.event_id = 10
        self.assertEqual('{"event_id": 10, "user_id": "test_user_id"}', str(event_option))
        event_option["plan"] = Plan(branch="test_branch", version_id="v1.1")
        self.assertEqual({"user_id": "test_user_id",
                          "event_id": 10,
                          "plan": {"branch": "test_branch", "versionId": "v1.1"}}, event_option.get_event_body())
        event = BaseEvent(event_type="test_event", event_properties={"properties1": "test"})
        self.assertTrue(isinstance(event, EventOptions))
        self.assertTrue(isinstance(event, BaseEvent))
        self.assertFalse(isinstance(event, IdentifyEvent))
        self.assertFalse(isinstance(event, GroupIdentifyEvent))
        self.assertFalse(isinstance(event, RevenueEvent))
        self.assertFalse("user_id" in event)
        self.assertFalse("plan" in event)
        self.assertFalse("device_id" in event)
        event.load_event_options(None)
        self.assertFalse("user_id" in event)
        self.assertFalse("plan" in event)
        self.assertFalse("device_id" in event)
        event.load_event_options(event_option)
        self.assertTrue("user_id" in event)
        self.assertTrue("plan" in event)
        self.assertFalse("device_id" in event)
        identify_event = IdentifyEvent()
        self.assertTrue(isinstance(identify_event, EventOptions))
        self.assertTrue(isinstance(identify_event, BaseEvent))
        self.assertTrue(isinstance(identify_event, IdentifyEvent))
        self.assertFalse(isinstance(identify_event, GroupIdentifyEvent))
        self.assertFalse(isinstance(identify_event, RevenueEvent))
        self.assertEqual(constants.IDENTIFY_EVENT, identify_event.event_type)
        group_identify_event = GroupIdentifyEvent()
        self.assertTrue(isinstance(group_identify_event, EventOptions))
        self.assertTrue(isinstance(group_identify_event, BaseEvent))
        self.assertFalse(isinstance(group_identify_event, IdentifyEvent))
        self.assertTrue(isinstance(group_identify_event, GroupIdentifyEvent))
        self.assertFalse(isinstance(group_identify_event, RevenueEvent))
        self.assertEqual(constants.GROUP_IDENTIFY_EVENT, group_identify_event.event_type)
        revenue_event = RevenueEvent()
        self.assertTrue(isinstance(revenue_event, EventOptions))
        self.assertTrue(isinstance(revenue_event, BaseEvent))
        self.assertFalse(isinstance(revenue_event, IdentifyEvent))
        self.assertFalse(isinstance(revenue_event, GroupIdentifyEvent))
        self.assertTrue(isinstance(revenue_event, RevenueEvent))
        self.assertEqual(constants.AMP_REVENUE_EVENT, revenue_event.event_type)

    def test_callback(self):
        def callback_func(event, code, message=None):
            self.assertEqual(event.event_type, "test_event")
            self.assertEqual(code, 200)
            self.assertEqual(message, "Test Message")

        test_event = BaseEvent("test_event", callback=callback_func)
        test_event.callback(200, "Test Message")

    def test_event_to_dict(self):
        event = BaseEvent(event_type="test_event", user_id="test_user", user_properties={"email": "test@test"})
        expect_dict = {"event_type": "test_event",
                       "user_id": "test_user",
                       "user_properties": {"email": "test@test"}}
        self.assertEqual(expect_dict, event.get_event_body())
        event["event_properties"] = {4: "4"}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": ["4", [5, 6]]}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": ["4", set()]}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": EventOptions()}
        self.assertFalse("event_properties" in event)
        event["event_properties"] = {"test": ["4", {"test": True}]}
        self.assertTrue("event_properties" in event)
        long_str = "acbdx" * 1000
        event["event_properties"] = {"test_long_str": long_str}
        expect_dict["event_properties"] = {"test_long_str": long_str[:constants.MAX_STRING_LENGTH]}
        self.assertEqual(expect_dict, event.get_event_body())
        event["event_properties"]["test_max_key"] = {}
        for i in range(2000):
            event["event_properties"]["test_max_key"][str(i)] = "test"
        expect_dict["event_properties"]["test_max_key"] = {}
        with self.assertLogs(None, "ERROR") as cm:
            self.assertEqual(expect_dict, event.get_event_body())
            self.assertEqual(['ERROR:amplitude.utils:Too many properties'], cm.output)
        list_properties = ["a", "c", 3, True]
        event["event_properties"]["list_properties"] = list_properties
        expect_dict["event_properties"]["list_properties"] = list_properties
        self.assertEqual(expect_dict, event.get_event_body())
        bool_properties = False
        event["event_properties"]["bool_properties"] = bool_properties
        expect_dict["event_properties"]["bool_properties"] = bool_properties
        self.assertEqual(expect_dict, event.get_event_body())
        float_properties = 26.92
        event["event_properties"]["float_properties"] = float_properties
        expect_dict["event_properties"]["float_properties"] = float_properties
        self.assertEqual(expect_dict, event.get_event_body())

    def test_identify_event(self):
        identify_obj = Identify()
        self.assertFalse(identify_obj.is_valid())
        expect_user_property = {}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.set("set_test_1", 15)
        expect_user_property[constants.IDENTITY_OP_SET] = {"set_test_1": 15}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        self.assertTrue(identify_obj.is_valid())
        with self.assertLogs(None, "ERROR") as cm:
            identify_obj.add("set_test_1", 6)
            self.assertEqual(expect_user_property, identify_obj.user_properties)
            self.assertEqual(['ERROR:amplitude.event:Key or clear all operation already set.'], cm.output)
        identify_obj.set_once("set_once_test", "test")
        expect_user_property[constants.IDENTITY_OP_SET_ONCE] = {"set_once_test": "test"}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.append("append_test", ["test1", "test2"])
        expect_user_property[constants.IDENTITY_OP_APPEND] = {"append_test": ["test1", "test2"]}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.prepend("prepend_test", False)
        expect_user_property[constants.IDENTITY_OP_PREPEND] = {"prepend_test": False}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.pre_insert("pre_insert_test", {"dict_test": "test_value"})
        expect_user_property[constants.IDENTITY_OP_PRE_INSERT] = {"pre_insert_test": {"dict_test": "test_value"}}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.post_insert("post_insert_test", 29.4)
        expect_user_property[constants.IDENTITY_OP_POST_INSERT] = {"post_insert_test": 29.4}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.remove("remove_test", "test")
        expect_user_property[constants.IDENTITY_OP_REMOVE] = {"remove_test": "test"}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.unset("unset_test")
        expect_user_property[constants.IDENTITY_OP_UNSET] = {"unset_test": constants.UNSET_VALUE}
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        identify_obj.add("add_test", "12")
        expect_user_property[constants.IDENTITY_OP_ADD] = {"add_test": "12"}
        self.assertNotEqual(expect_user_property, identify_obj.user_properties)
        expect_user_property[constants.IDENTITY_OP_ADD]["add_test"] = 12
        identify_obj.add("add_test", 12)
        self.assertEqual(expect_user_property, identify_obj.user_properties)
        event = IdentifyEvent(identify_obj=identify_obj)
        self.assertTrue(event, IdentifyEvent)
        self.assertEqual(event.event_type, constants.IDENTIFY_EVENT)
        identify_obj.clear_all()
        self.assertEqual({constants.IDENTITY_OP_CLEAR_ALL: "-"}, identify_obj.user_properties)
        self.assertEqual(expect_user_property, event.user_properties)

    def test_group_identify_event(self):
        identify_obj = Identify()
        expect_group_property = {}
        identify_obj.set("set_test_1", 15)
        expect_group_property[constants.IDENTITY_OP_SET] = {"set_test_1": 15}
        identify_obj.set_once("set_once_test", "test")
        expect_group_property[constants.IDENTITY_OP_SET_ONCE] = {"set_once_test": "test"}
        identify_obj.append("append_test", ["test1", "test2"])
        expect_group_property[constants.IDENTITY_OP_APPEND] = {"append_test": ["test1", "test2"]}
        identify_obj.post_insert("post_insert_test", 29.4)
        expect_group_property[constants.IDENTITY_OP_POST_INSERT] = {"post_insert_test": 29.4}
        self.assertEqual(expect_group_property, identify_obj.user_properties)
        event = GroupIdentifyEvent(identify_obj=identify_obj)
        self.assertTrue(isinstance(event, GroupIdentifyEvent))
        self.assertEqual(expect_group_property, event.group_properties)

    def test_revenue_event(self):
        revenue_obj = Revenue(price="30.65", quantity=2, product_id="test_product_id",
                              revenue_type="test_revenue_type")
        self.assertFalse(revenue_obj.is_valid())
        revenue_obj.price = 30.65
        self.assertTrue(revenue_obj.is_valid())
        expect_event_properties = {constants.REVENUE_PRICE: 30.65,
                                   constants.REVENUE_QUANTITY: 2,
                                   constants.REVENUE_PRODUCT_ID: "test_product_id",
                                   constants.REVENUE_TYPE: "test_revenue_type"}
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())
        revenue_obj.set_receipt("test_receipt", "test_receipt_signature")
        self.assertEqual("test_receipt", revenue_obj.receipt)
        self.assertEqual("test_receipt_signature", revenue_obj.receipt_sig)
        expect_event_properties[constants.REVENUE_RECEIPT] = "test_receipt"
        expect_event_properties[constants.REVENUE_RECEIPT_SIG] = "test_receipt_signature"
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())
        revenue_obj.properties = {"other_properties": "test", "other_properties2": 2}
        expect_event_properties["other_properties"] = "test"
        expect_event_properties["other_properties2"] = 2
        self.assertEqual(expect_event_properties, revenue_obj.get_event_properties())
        event = revenue_obj.to_revenue_event()
        event2 = RevenueEvent(revenue_obj=revenue_obj)
        self.assertTrue(isinstance(event, RevenueEvent))
        self.assertTrue(isinstance(event2, RevenueEvent))
        self.assertEqual(event.get_event_body(), event2.get_event_body())
        self.assertEqual(constants.AMP_REVENUE_EVENT, event.event_type)
        self.assertEqual(expect_event_properties, event.event_properties)

    def test_plan(self):
        plan = Plan(branch="branch-1", source="Python", version=5, version_id="xyz")
        expect_plan = {"branch": "branch-1", "source": "Python", "version": "5", "versionId": "xyz"}
        with self.assertLogs(None, "ERROR") as cm:
            plan_dict = plan.get_plan_body()
            self.assertTrue(isinstance(plan_dict, dict))
            self.assertNotEqual(expect_plan, plan_dict)
            self.assertEqual(["ERROR:amplitude.event:plan.version value type: <class 'int'>. Expect <class 'str'>"],
                             cm.output)
        plan.version = "5"
        event = BaseEvent("test_event", plan=plan)
        self.assertEqual({"event_type": "test_event", "plan": expect_plan}, event.get_event_body())
        self.assertTrue("plan" in event)


if __name__ == '__main__':
    unittest.main()
