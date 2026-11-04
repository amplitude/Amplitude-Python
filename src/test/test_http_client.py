import http.client
import unittest
from unittest import mock

from amplitude.http_client import HttpClient, HttpStatus

# Other test modules replace HttpClient.post with a mock and do not restore it,
# so keep a reference to the real implementation.
http_post = HttpClient.post


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body


class HttpClientTestCase(unittest.TestCase):
    def post_with_urlopen(self, **urlopen_kwargs):
        with mock.patch("urllib.request.urlopen", **urlopen_kwargs):
            return http_post("https://api2.amplitude.com/2/httpapi", b"{}")

    def test_post_success(self):
        res = self.post_with_urlopen(return_value=FakeResponse(b'{"code": 200}'))
        self.assertEqual(HttpStatus.SUCCESS, res.status)
        self.assertEqual(200, res.code)

    def test_post_connection_errors_after_request_sent_are_unknown(self):
        errors = [
            http.client.RemoteDisconnected("Remote end closed connection without response"),
            ConnectionResetError(104, "Connection reset by peer"),
            http.client.IncompleteRead(b"{\"co"),
        ]
        for exc in errors:
            with self.subTest(exc=type(exc).__name__):
                res = self.post_with_urlopen(side_effect=exc)
                self.assertEqual(HttpStatus.UNKNOWN, res.status)
                self.assertEqual(-1, res.code)
                self.assertTrue(res.error)

    def test_post_unexpected_response_body_is_unknown(self):
        for body in (b"<html>502 Bad Gateway</html>", b'{"events_ingested": 1}'):
            with self.subTest(body=body):
                res = self.post_with_urlopen(return_value=FakeResponse(body))
                self.assertEqual(HttpStatus.UNKNOWN, res.status)
                self.assertTrue(res.error)


if __name__ == '__main__':
    unittest.main()
