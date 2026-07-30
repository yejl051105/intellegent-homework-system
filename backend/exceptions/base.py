"""应用异常根类。

业务码和 HTTP 状态码是两个独立维度：前者给前端识别业务结果，
后者表达 HTTP 层的请求结果，不能互相复用。
"""


class BaseAppException(Exception):
    code: int = 10000
    message: str = "业务异常"
    http_status: int = 400

    # * 后面的参数强制要求使用参数名传递，防止调用者传错顺序，提高代码可读性
    def __init__(
        self,
        message: str | None = None,
        *,
        code: int | None = None,
        http_status: int | None = None,
    ):
        self.code = self.__class__.code if code is None else code
        self.message = self.__class__.message if message is None else message
        self.http_status = (
            self.__class__.http_status if http_status is None else http_status
        )
        super().__init__(self.message)
