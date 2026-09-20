import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from model.batch import Batch


class BatchDelivery:
    def __init__(self, endpoint: str, token: str, timeout: float = 10.0) -> None:
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout

    def send(self, batch: Batch) -> bool:
        request = Request(
            self.endpoint,
            data=_encode_batch(batch),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.status == 202
        except (HTTPError, URLError):
            return False


def _encode_batch(batch: Batch) -> bytes:

    return json.dumps(batch.to_dict(), ensure_ascii=False).encode("utf-8")
