import unittest
from app import app
from bot.engine import bot
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index_page(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'<title>SEO Traffic Booster Pro</title>', rv.data)

    def test_stats_api(self):
        rv = self.client.get('/api/stats')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertIn('visits', data)
        self.assertFalse(data['is_running'])

    def test_bot_start_stop_logic(self):
        rv = self.client.post('/api/bot/stop')
        self.assertEqual(rv.status_code, 400)
        
if __name__ == '__main__':
    unittest.main()
