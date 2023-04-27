import flask
import flask_restful
from flask import Flask
from werkzeug.exceptions import HTTPException

from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import ApiException
from backend.utils.logging_utils import init_logging
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from backend.config import USERNAME, PORT, PASSWORD, DATABASE, HOST
from flask_login import LoginManager
from backend.utils.make_response_utils import make_response, make_exception_response

# 初始化日志器
init_logging()
# 初始化flask对象
app = Flask(__name__)

# 配置sqlalchemy的uri（连接数据库的URL）
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_POOL_SIZE'] = 100

# 配置SECRET
app.config['SECRET_KEY'] = "jaldjf31asdfzx2"
# 创建SQLAlchemy的对象
db = SQLAlchemy(app)
# 初始化flask restful
handle_exception_temp = app.handle_exception # 备份Flask的异常代码
handle_user_exception_temp = app.handle_user_exception
api = Api(app)  # 执行这个后，Api会重写app.handle_exception app.handle_user_exception
app.handle_exception = handle_exception_temp # 还原Flask的异常处理代码
app.handle_user_exception = handle_user_exception_temp
# 初始化登陆
login_manager = LoginManager()
login_manager.init_app(app)

@app.errorhandler(400)
def abort_400(errors):
    app.logger.info(errors)
    return make_response("400")


@app.errorhandler(401)
def abort_401(errors):
    app.logger.info(errors)
    return make_response("401")


@app.errorhandler(403)
def abort_403(errors):
    app.logger.info(errors)
    return make_response("403")


@app.errorhandler(404)
def abort_404(errors):
    app.logger.info(errors)
    return make_response("404")


@app.errorhandler(500)
def abort_500(errors):
    app.logger.info(errors)
    return make_response("500")


# 全局异常捕获（能够捕获所有的异常，未知异常要看日志）
@app.errorhandler(Exception)
def framework_error(errors):
    if isinstance(errors, ApiException):  # 如果异常是我们自定义的ApiException，那么直接返回结果
        return errors
    if isinstance(errors, HTTPException):  # 如果异常是框架中定义的HTTPException，那么我们捕获这个异常
        code = errors.code
        message = errors.description
        return ApiException(code, message)
    else:
        app.logger.info(errors)
        return make_exception_response(CodeUtil.UN_KNOW_ERROR)

