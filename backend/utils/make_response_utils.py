import json

from backend.utils.code_utils import CodeUtil
from flask import Response


# 响应数据
def make_response(status=CodeUtil.SUCCESS,msg=None, data=None, **kwargs):
    response_data = {"status": status, "msg": msg if msg else CodeUtil.MSG[status], "data": data}
    if kwargs:
        for k, v in kwargs.items():
            if k == "total_count":
                response_data.update({k: v})
            if k == "page":
                response_data.update({k: v})
            if k == "size":
                response_data.update({k: v})
    return Response(json.dumps(response_data), mimetype="application/json")


# 用于异常返回的响应数据
def make_exception_response(status=CodeUtil.SUCCESS, msg=None, data=None):
    return json.dumps({"status": str(status), "msg": msg if msg else CodeUtil.MSG[str(status)], "data": data})
