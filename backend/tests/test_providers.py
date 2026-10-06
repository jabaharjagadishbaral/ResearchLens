import unittest, urllib.error

from app.core.config import Settings
from app.core.security import ServiceError
from app.providers.base import GenerationRequest
from app.providers.local import ExtractiveLLM
from app.providers.remote import OpenAICompatibleLLM, build_providers


class Fake(OpenAICompatibleLLM):
    def __init__(self, responses):
        super().__init__("http://x/v1/", "m", "k", retries=1)
        self.responses, self.sent = list(responses), []

    def _post(self, payload):
        self.sent.append(payload)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class ProviderTests(unittest.TestCase):
    def test_payload_and_success_after_retry(self):
        import app.providers.remote as m
        m.time.sleep = lambda s: None
        f = Fake([urllib.error.URLError("down"), {"choices": [{"message": {"content": "ok [1]"}}]}])
        out = f.generate(GenerationRequest("sys", "usr", "q"))
        self.assertEqual(out, "ok [1]")
        self.assertEqual(f.sent[0]["messages"][0], {"role": "system", "content": "sys"})
        self.assertTrue(f.url.endswith("/v1/chat/completions"))

    def test_failure_maps_to_user_safe_error(self):
        import app.providers.remote as m
        m.time.sleep = lambda s: None
        with self.assertRaises(ServiceError) as e:
            Fake([urllib.error.URLError("a"), urllib.error.URLError("b")]).generate(GenerationRequest("s", "u", "q"))
        self.assertEqual(e.exception.message, "The model provider did not respond. Please retry.")

    def test_factory(self):
        self.assertIsInstance(build_providers(Settings())[2], ExtractiveLLM)
        with self.assertRaises(ValueError):
            build_providers(Settings(llm_provider="nope"))
        with self.assertRaises(ValueError):
            build_providers(Settings(llm_provider="openai"))   # missing base url/model


if __name__ == "__main__":
    unittest.main()
