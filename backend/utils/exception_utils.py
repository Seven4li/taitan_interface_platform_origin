from werkzeug.exceptions import HTTPException

from backend.utils.make_response_utils import make_response, make_exception_response


class ApiException(HTTPException):
    code = 500
    message = "Server Interal Error"

    def __init__(self, code=None, message=None):
        if code:
            self.code = code
        if message:
            self.message = message
        super(ApiException, self).__init__(self.message, None)

    def get_body(self, environ=None, *args, **kwargs):
        return make_exception_response(self.code, self.message)

    def get_headers(self, environ=None, *args, **kwargs):
        return [('Content-Type', 'application/json')]


class REQ_IS_EMPTY_ERROR(ApiException):
    code = 400
    message = "请求数据不能为空"


class REQ_TYPE_ERROR(ApiException):
    code = 400
    message = "请求类型不正确"


class REQ_VALUE_ERROR(ApiException):
    code = 400
    message = "请求数据的值类型不正确"


class REQ_KEY_ERROR(ApiException):
    code = 400
    message = "缺少必填参数"
