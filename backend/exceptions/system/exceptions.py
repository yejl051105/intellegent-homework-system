"""系统异常：Redis、数据库、OCR、模型等基础设施或第三方服务。"""

from backend.exceptions.base import BaseAppException


class SystemException(BaseAppException):
    code = 50000
    message = "系统内部错误"
    http_status = 500

    def __init__(self, message: str | None = None, **kwargs):
        self.log_message = message or self.__class__.message
        # message 只用于日志，响应使用异常类定义的稳定脱敏文案。
        super().__init__(None, **kwargs)


class RedisException(SystemException):
    code = 50001
    message = "缓存服务暂时不可用"
    http_status = 503


class DatabaseException(SystemException):
    code = 50002
    message = "数据库服务暂时不可用"
    http_status = 503


class ThirdPartyServiceException(SystemException):
    code = 50003
    message = "第三方服务暂时不可用"
    http_status = 502


class ModelConfigurationError(ThirdPartyServiceException):
    code = 50004
    message = "模型服务配置不可用"
    http_status = 503


class ModelResponseError(ThirdPartyServiceException):
    code = 50005
    message = "模型服务处理失败"
    http_status = 502
