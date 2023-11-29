from sanic_ext.extensions.openapi.definitions import RequestBody, Response


class ReqBody(RequestBody):
    def __init__(
        self,
        content,
        required=True,
        **kwargs,
    ):
        super().__init__(
            content={"application/json": content},
            required=required,
            **kwargs,
        )


class ResBody(Response):
    def __init__(
        self,
        content,
        status=200,
        **kwargs,
    ):
        super().__init__(
            content={"application/json": content},
            status=status,
            **kwargs,
        )
