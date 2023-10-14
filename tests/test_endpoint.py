import io
import json
import unittest
from pathlib import Path

from server import app


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.test_speech_path = str(Path(__file__).parent / "data" / "test.mp3")

    def test_recognise_endpoint(self):
        with self.app.app_context():
            with self.client as client:
                # Create a test m4a file
                with open(self.test_speech_path, 'rb') as f:
                    audio_file = f.read()
                data = {
                    'm4a_file': (io.BytesIO(audio_file), 'test.m4a'),
                    'smart_mode': 'false'
                }
                response = client.post('/recognise', content_type='multipart/form-data', data=data)
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200, data["error"])
                self.assertIn('transcript', data)
                self.assertEqual(data["transcript"], 'Replace world with planet.')

    def test_edit_endpoint(self):
        with self.app.app_context():
            with self.client as client:
                # Create a test m4a file
                with open(self.test_speech_path, 'rb') as f:
                    audio_file = f.read()
                data = {
                    'm4a_file': (io.BytesIO(audio_file), 'test.m4a'),
                    'text': 'hello world'
                }
                response = client.post('/edit', content_type='multipart/form-data', data=data)
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200, data["error"])
                self.assertIn('transcript', data)
                self.assertEqual(data["transcript"], 'Hello planet.')

    def test_recognise_endpoint_no_file(self):
        with self.app.app_context():
            with self.client as client:
                data = {
                    'smart_mode': 'true'
                }
                response = client.post('/recognise', content_type='multipart/form-data', data=data)
                self.assertEqual(response.status_code, 400)

    def test_edit_endpoint_no_file(self):
        with self.app.app_context():
            with self.client as client:
                data = {
                    'text': 'This is a test text.'
                }
                response = client.post('/edit', content_type='multipart/form-data', data=data)
                self.assertEqual(response.status_code, 400)

    def test_recognise_endpoint_no_smart_mode(self):
        with self.app.app_context():
            with self.client as client:
                # Create a test m4a file
                data = {
                    'm4a_file': (io.BytesIO(b"abcdef"), 'test.m4a'),
                }
                response = client.post('/recognise', content_type='multipart/form-data', data=data)
                self.assertEqual(response.status_code, 400)

    def test_edit_endpoint_no_text(self):
        with self.app.app_context():
            with self.client as client:
                # Create a test m4a file
                data = {
                    'm4a_file': (io.BytesIO(b"abcdef"), 'test.m4a'),
                }
                response = client.post('/edit', content_type='multipart/form-data', data=data)
                self.assertEqual(response.status_code, 400)
