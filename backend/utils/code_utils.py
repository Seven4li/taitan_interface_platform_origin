class CodeUtil:
    SUCCESS = "1"
    FAIL = "-1"
    ERROR = "-9999"

    REQ_IS_EMPTY_ERROR = "-2"
    REQ_TYPE_ERROR = "-3"
    REQ_VALUE_ERROR = "-4"
    REQ_KEY_ERROR = "-5"

    REQ_ERROR = "400"
    UN_AUTH = "401"
    FORBIDDEN = "403"
    NOT_FOUND = "404"
    SERVER_ERROR = "500"

    UN_KNOW_ERROR = "-10000"
    MSG = {
        SUCCESS: "成功",
        FAIL: "失败",
        ERROR: "异常",
        REQ_IS_EMPTY_ERROR: "请求数据不能为空",
        REQ_TYPE_ERROR: "请求数据类型错误",
        REQ_VALUE_ERROR: "请求数据的值类型错误",
        REQ_KEY_ERROR: "缺少必填参数",
        REQ_ERROR: "400 请求数据错误",
        UN_AUTH: "401 请求没有得到授权错误",
        FORBIDDEN: "403 请求是被禁止的",
        NOT_FOUND: "404 请求的资源不存在",
        SERVER_ERROR: "500 服务器内部错误",
        UN_KNOW_ERROR:"未知错误，请联系开发人员分析",

    }
