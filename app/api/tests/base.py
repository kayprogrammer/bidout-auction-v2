from sanic_testing.testing import SanicTestClient, TestingResponse
from sanic.request import Request
import typing


class CustomSanicTestClient(SanicTestClient):
    headers = {}

    def _sanic_endpoint_test(
        self, *args, **kwargs
    ) -> typing.Tuple[typing.Optional[Request], typing.Optional[TestingResponse]]:
        request_headers = kwargs.get("headers")
        if not request_headers:
            kwargs.update({"headers": self.headers})

        return super()._sanic_endpoint_test(*args, **kwargs)
