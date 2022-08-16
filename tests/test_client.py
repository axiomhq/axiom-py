import os
import unittest
import responses
from axiom import Client


class TestClient(unittest.TestCase):

    client: Client

    @classmethod
    def setUpClass(cls):
        cls.client = Client(
            os.getenv("AXIOM_TOKEN"),
            os.getenv("AXIOM_ORG_ID"),
            os.getenv("AXIOM_URL"),
        )

    @responses.activate
    def test_retries(self):
        url = os.getenv("AXIOM_URL") + "/api/v1/datasets/test"
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, status=502)
        responses.add(
            responses.GET,
            url,
            status=200,
            json={"name": "test", "description": "", "who": "", "created": ""},
        )

        resp = self.client.datasets.get("test")
        assert len(responses.calls) == 3
