import json

from django.test import TestCase


class AdminApiTests(TestCase):
    '''
    Open ONI Admin API
    '''

    def test_description_json(self):
        r = self.client.get('/api/admin/')
        self.assertEqual(r.status_code, 200)
        j = json.loads(r.content)
        self.assertEqual(j['description'], 'Open ONI Admin API for automating management tasks')
        self.assertEqual(j['title'], 'Open ONI Admin API')
