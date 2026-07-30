"""业务异常：用户、订单、认证及通用业务规则。"""

from backend.exceptions.base import BaseAppException


class BusinessException(BaseAppException):
    code = 11000
    message = "业务异常"
    http_status = 400


class ResourceNotFoundException(BusinessException):
    code = 11001
    message = "资源不存在"
    http_status = 404


class BusinessValidationException(BusinessException):
    code = 11002
    message = "业务参数校验失败"
    http_status = 422


class BusinessConflictException(BusinessException):
    code = 11003
    message = "当前业务状态不允许该操作"
    http_status = 409


class CriteriaExtractionError(BusinessException):
    code = 11004
    message = "评分标准附件处理失败"
    http_status = 422


class UserException(BusinessException):
    code = 10100
    message = "用户业务异常"
    http_status = 400


class UserNotFoundException(UserException):
    code = 10101
    message = "用户不存在"
    http_status = 404


class OrderException(BusinessException):
    code = 10300
    message = "订单业务异常"
    http_status = 400


class OrderNotFoundException(OrderException):
    code = 10301
    message = "订单不存在"
    http_status = 404


class OrderStateException(OrderException):
    code = 10302
    message = "当前订单状态不允许该操作"
    http_status = 409


class AuthException(BusinessException):
    code = 10000
    message = "认证业务异常"
    http_status = 401


class NotLoginException(AuthException):
    code = 10001
    message = "未登录"
    http_status = 401


class TokenExpiredException(AuthException):
    code = 10002
    message = "Token 已过期"
    http_status = 401


class PermissionDeniedException(AuthException):
    code = 10003
    message = "无权访问该资源"
    http_status = 403


class PasswordMismatchException(AuthException):
    code = 10102
    message = "密码错误"
    http_status = 401
