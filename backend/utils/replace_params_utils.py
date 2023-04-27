# -*- encoding=utf-8 -*-
# 替换请求数据中的变量：
# 请求数据：request_data : 请求方法、HOST、PORT、资源路径、查询参数、请求头、请求体、预期数据
# 环境变量：env_data ： {"params_key":"params_value", "params_key":"params_value"}
# 假设request_data = {{host}} ，env_data = {"host":"10.1.201.231"}
# 提取{{host}}中的host，为a = "host" env_data.get(a) 相当于 env_data.get("host")
# 替换{{host}}的值为10.1.201.231
import re

from backend.app import app


def replace_params(request_data, env_data):
    app.logger.info(f"替换环境变量之前的请求数据为：{request_data}")
    if not isinstance(request_data, str): # 增加检查要替换的数据是不是字符串（原因：re只能处理字符串）
        request_data = str(request_data) # 把数据转化为字符串
    # 使用正则表达式提取request_data当中的变量
    patter_params = '{{([a-zA-Z0-9_]+?)}}' # 能够匹配{{变量名}}中的变量名的正则表达式
    # 匹配请求数据
    match_result_list = re.findall(patter_params, request_data)
    app.logger.info(match_result_list)
    # 提取环境的dict数据，这个数据是直接通过形式传递传递的
    _env_data = env_data
    # 通过for循环，遍历提取出来的所有变量，然后使用环境数据提取对应变量的值，如果提取不到，那么原样返回
    value_list = []
    for params in match_result_list:
        value = _env_data.get(params)
        app.logger.info(value)
        if value is None: # 如果环境中没有匹配到这个变量，那么原样返回
            value = "{{" +params+ "}}"
        value_list.append(value) # 把提取出来的所有变量按照顺序放在value_list中
    app.logger.info(value_list)
    # 替换请求数据当中的变量，例如{{host}}要替换为10.1.201.232
    # 切分变量数据，按照正则表达式匹配的变量去切分
    patter_split = '{{[a-zA-Z0-9_]+?}}'
    split_result = re.split(patter_split, request_data)
    app.logger.info(split_result)
    # 组合的字符串
    combine_str = ""
    for i in range(len(split_result)):
        if i == 0:
            combine_str = split_result[0]
        if i > 0:
            combine_str += value_list[i-1]
            combine_str += split_result[i]
    app.logger.info(f"替换之后的数据为: {combine_str}")

    return combine_str


if __name__ == '__main__':
    request_data = '{"mobile": {{mobile}}, "password": {{password}}}'
    env_data = {"mobile":"15100000002", "password":"123456"}
    replace_params(request_data, env_data)