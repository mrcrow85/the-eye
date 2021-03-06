import json
from unittest.mock import patch
from django.http import QueryDict

from django.test import TestCase

from the_eye.models import Event
from the_eye.serializers import EventSerializer


class EventListTests(TestCase):
    @patch("the_eye.views.save_event.delay")
    def test_create_event(self, mock_async_task):
        mock_async_task.return_value = None
        event_data = {
            'session_id': '123',
            'category': 'page_interaction',
            'name': 'page_view',
            'data': json.dumps({
                "host": "www.consumeraffairs.com",
                "path": "/",
            }),
            'timestamp': '2022-01-01 00:00:00.000000'
        }
        response = self.client.post('/events/', event_data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(mock_async_task.called)
        self.assertEquals(mock_async_task.call_args[0][0].dict(), event_data)

    def test_list_events(self):
        Event.objects.bulk_create(
            [
                Event(session_id='123', category='test', name='test', data=json.dumps({'test': f'test{i}'}))
                for i in range(10)
            ]
        )
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [EventSerializer(event).data for event in Event.objects.all().iterator()])

    def test_list_events_by_session(self):
        Event.objects.bulk_create(
            [
                Event(session_id=f'123{i}', category='test', name='test', data=json.dumps({'test': f'test{i}'}))
                for i in range(10)
            ]
        )
        response = self.client.get('/events?session_id=1230')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [EventSerializer(Event.objects.get(session_id='1230')).data])

    def test_list_events_by_category(self):
        Event.objects.bulk_create(
            [
                Event(session_id=f'123{i}', category=f'test{i}', name='test', data=json.dumps({'test': f'test{i}'}))
                for i in range(10)
            ]
        )
        response = self.client.get('/events?category=test0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'], [EventSerializer(Event.objects.get(category='test0')).data])

    def test_list_events_by_timestamp_range(self):
        Event.objects.bulk_create(
            [
                Event(session_id=f'123{i}', category=f'test{i}', name='test', data=json.dumps({'test': f'test{i}'}), timestamp=f'2022-01-01 00:00:00.{i}')
                for i in range(10)
            ]
        )
        response = self.client.get('/events?start_time=2022-01-01 00:00:00.0&end_time=2022-01-01 00:00:00.2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'],
            [
                EventSerializer(event).data
                for event in Event.objects.filter(timestamp__range=('2022-01-01 00:00:00.0', '2022-01-01 00:00:00.2'))
            ]
        )
        response_iso = self.client.get('/events?start_time=2022-01-01T00%3A00%3A00.0&end_time=2022-01-01T00%3A00%3A00.2')
        self.assertEqual(response_iso.status_code, 200)
        self.assertEqual(
            response_iso.json()['results'],
            [
                EventSerializer(event).data
                for event in Event.objects.filter(timestamp__range=('2022-01-01 00:00:00.0', '2022-01-01 00:00:00.2'))
            ]
        )

    def test_list_events_by_all_params(self):
        Event.objects.bulk_create(
            [
                Event(session_id=f'123{i}', category=f'test{i}', name='test', data=json.dumps({'test': f'test{i}'}), timestamp=f'2022-01-01 00:00:00.{i}')
                for i in range(10)
            ]
        )
        response = self.client.get('/events?session_id=1230&category=test0&start_time=2022-01-01 00:00:00.0&end_time=2022-01-01 00:00:00.2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['results'],
            [
                EventSerializer(event).data
                for event in Event.objects.filter(
                    session_id='1230',
                    category='test0',
                    timestamp__range=('2022-01-01 00:00:00.0', '2022-01-01 00:00:00.2')
                )
            ]
        )
