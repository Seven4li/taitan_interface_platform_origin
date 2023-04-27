# -*- encoding=utf-8 -*-
import json
import logging

from flask import Flask, request, jsonify

app = Flask(__name__)
import xlrd


@app.route('/api/upload', methods=['POST'])
# 上传文件
def excel_upload():
    '''
    :param request:
    :return: 上传文件excel表格 ,并进行解析
    '''
    if request.method == "POST":
        result = None
        f = request.files['file']
        print(f.filename)
        type_excel = f.filename.split('.')[1]
        print("type_excel: ", type_excel)
        if 'xlsx' == type_excel or 'xls' == type_excel:
            # 开始解析上传的excel表格
            workbook = xlrd.open_workbook(filename=None, file_contents=f.read())  # 关键点在于这里
            sheet1 = workbook.sheet_by_index(0)
            nrows = sheet1.nrows
            idx = sheet1.row_values(0)
            # 最终的数据列表
            data = []

            # 从第1行开始遍历循环所有行，获取每行的数据
            for i in range(1, nrows):
                row_data = sheet1.row_values(i)
                # 组建每一行数据的字典
                row_data_dict = {}
                # 遍历行数据的每一项，赋值进行数据字典
                for j in range(len(row_data)):
                    item = row_data[j]
                    row_data_dict[idx[j]] = item
                # 将行数据字典加入到data列表中
                data.append(row_data_dict)
                result = json.dumps(data, indent=4, ensure_ascii=False)

        return jsonify({"status": "ok", "msg": "成功", "data": result})
    return jsonify({"status": "fail", "msg": "你是不是没有用post请求方法？"})

# 直接调用该接口即可导出文件
@app.route("/exportExcel", methods=["GET", "POST"])
def export_excel_inter():
    """导出excel报表"""
    return export_excel()

import time
from io import BytesIO
from flask import send_file
import xlwt

def export_excel():
    """excel 报表导出"""
    wb = xlwt.Workbook()
    sheet = wb.add_sheet("测试套件")

    # 使用字节流存储
    output = BytesIO()

    # 保存文件
    wb.save(output)

    # 文件seek位置，从头(0)开始
    output.seek(0)
    filename = "测试套件 %s.xls" % str(int(time.time()))

    # 打印文件大小
    logging.info("{} -> {} b".format(filename, len(output.getvalue())))

    # as_attachment：是否在headers中添加Content-Disposition
    # attachment_filename：下载时使用的文件名
    # conditional: 是否支持断点续传
    fv = send_file(output, as_attachment=True, attachment_filename=filename, conditional=True)
    fv.headers['Content-Disposition'] += "; filename*=utf-8''{}".format(filename)
    fv.headers["Cache-Control"] = "no_store"
    fv.headers["max-age"] = 1

    logging.info("导出报表---------%s" % filename)

    return fv

if __name__ == '__main__':
    app.run()
