import copy
import enum
import unittest

from amplitude import BaseEvent, constants


class PropertyValue(enum.Enum):
    EXAMPLE = 'example'


class EventSerializationTestCase(unittest.TestCase):
    def assert_properties_preserved(self, field):
        properties = {
            'empty': None,
            'value': PropertyValue.EXAMPLE,
            'nested': {'text': 'x' * (constants.MAX_STRING_LENGTH + 1)},
            'items': [{'text': 'y' * (constants.MAX_STRING_LENGTH + 1)}],
        }
        original = copy.deepcopy(properties)
        event = BaseEvent('example', user_id='user', **{field: properties})

        body = event.get_event_body()

        self.assertEqual(original, properties)
        self.assertEqual(original, getattr(event, field))
        self.assertEqual('x' * constants.MAX_STRING_LENGTH, body[field]['nested']['text'])
        self.assertEqual('y' * constants.MAX_STRING_LENGTH, body[field]['items'][0]['text'])
        if field != 'groups':
            self.assertNotIn('empty', body[field])
            self.assertEqual('example', body[field]['value'])

    def test_event_properties_preserved(self):
        self.assert_properties_preserved('event_properties')

    def test_user_properties_preserved(self):
        self.assert_properties_preserved('user_properties')

    def test_group_properties_preserved(self):
        self.assert_properties_preserved('group_properties')

    def test_groups_preserved(self):
        self.assert_properties_preserved('groups')

    def test_serialized_body_can_be_modified_independently(self):
        properties = {'nested': {'value': 'original'}, 'items': ['original']}
        event = BaseEvent('example', event_properties=properties)
        body = event.get_event_body()
        body['event_properties']['nested']['value'] = 'changed'
        body['event_properties']['items'].append('changed')
        self.assertEqual({'nested': {'value': 'original'}, 'items': ['original']}, properties)
        self.assertEqual(properties, event.event_properties)

    def test_repeated_serialization_returns_same_payload(self):
        event = BaseEvent('example', event_properties={'empty': None, 'value': PropertyValue.EXAMPLE})
        self.assertEqual(event.get_event_body(), event.get_event_body())

    def test_false_zero_and_empty_containers_remain_in_payload(self):
        properties = {'false': False, 'zero': 0, 'list': [], 'dict': {}}
        body = BaseEvent('example', event_properties=properties).get_event_body()
        self.assertEqual(properties, body['event_properties'])
