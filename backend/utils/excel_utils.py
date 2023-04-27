# -*- encoding=utf-8 -*-
import json
from io import BytesIO

import xlrd
import xlwt
from backend.app import app
from backend.config import BASE_DIR


class ExcelUtils:
    def __init__(self):
        # 创建一个工作簿
        self.xl = xlwt.Workbook(encoding='utf-8')
        # 设置RGB颜色
        self.xl.set_colour_RGB(0x21, 255, 217, 102)
        # 创建一个sheet对象,第二个参数是指单元格是否允许重设置，默认为False
        self.sheet = self.xl.add_sheet('测试用例', cell_overwrite_ok=True)
        # 设置列宽
        for i in range(20):
            self.sheet.col(i).width = 25 * 256

        # 初始化样式
        self.style1 = xlwt.XFStyle()  # 标题样式
        self.style2 = xlwt.XFStyle()  # 内容样式
        # 设置边框
        # 细实线:1，小粗实线:2，细虚线:3，中细虚线:4，大粗实线:5，双线:6，细点虚线:7
        # 大粗虚线:8，细点划线:9，粗点划线:10，细双点划线:11，粗双点划线:12，斜点划线:13
        borders = xlwt.Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1
        self.style1.borders = borders

        # 设置单元格对齐方式
        alignment = xlwt.Alignment()
        # 0x01(左端对齐)、0x02(水平方向上居中对齐)、0x03(右端对齐)
        alignment.horz = 0x02
        # 0x00(上端对齐)、 0x01(垂直方向上居中对齐)、0x02(底端对齐)
        alignment.vert = 0x01
        # 设置自动换行
        alignment.wrap = 1
        self.style1.alignment = alignment

        # 为样式创建字体
        self.font = xlwt.Font()
        self.font.name = '微软雅黑'
        # 黑体
        self.font.bold = True
        # 下划线
        self.font.underline = False
        # 斜体字
        self.font.italic = False
        # 字体大小
        self.font.height = 20 * 15
        # 创建背景模式对象
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = 22
        # 设置背景颜色
        self.style1.pattern = pattern
        # 设定样式
        self.style1.font = self.font

        self.style2.alignment = alignment

    def export_data(self, data):
        app.logger.info(f"导出数据开始，准备导出的数据是：{data}")
        # 定义要保存的IO流
        output = BytesIO()
        try:
            case_headers = list(data[0].keys())
            # 保存测试用例的标题
            for i in range(len(case_headers)):
                # 第一个参数代表行，第二个参数是列，第三个参数是内容，第四个参数是格式
                self.sheet.write(0, i, case_headers[i], self.style1)
            # 保存数据
            for i in range(len(data)):
                test_case = data[i]
                for j in range(len(test_case.values())):
                    test_case_element = list(test_case.values())
                    self.sheet.write(i + 1, j, str(test_case_element[j]), self.style2)

            # 保存excel中的数据到output中
            self.xl.save(output)
            return output
        except Exception as e:
            app.logger.info(e)
            return output

    def import_case(self, file=None):
        """
        :param file: IO流
        :return:
        """
        workbook = xlrd.open_workbook(filename=None, file_contents=file.read()) # 完成远程导入的核心
        sheet1 = workbook.sheet_by_index(0)
        nrows = sheet1.nrows

        idx = sheet1.row_values(0)
        # 最终的数据列表
        data = []
        result = None
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

        return result

    # 将读取的数据转化为json
    def readexcel(self, file):
        workbook = xlrd.open_workbook(file)
        sheet1 = workbook.sheet_by_index(0)
        nrows = sheet1.nrows

        idx = sheet1.row_values(0)
        # 最终的数据列表
        data = []
        result = None
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
        # print(result)
        return result

    def foramt_data(self, case_data_list):
        # 把case_data_list中，字符串'None'转化为 None
        for case_data in case_data_list:
            for key,value in case_data.items():
                if value == 'None':
                    case_data[key] = None

        return case_data_list

if __name__ == '__main__':
    excel_util = ExcelUtils()
    case_data = [
        {
            'id': '1',
            'case_name': '密码错误',
            'request_method': 'POST',
            'request_url': 'http://10.1.201.231:8080/ssm_web/user/login',
            'request_params': {'phone': '', 'password': '1234567'},
            'request_headers': {'Content-Type': 'application/json'},
            'request_body': {},
            'description': '拉勾商城登录成功',
            'predict': None,
            'suite_id': 1,
            'projectid': 1,
            'isDeleted': False,
            'status': True,
            'createTime': '2021-11-26 22:30:59',
            'lastUpdateTime': 'None'
        },
        {
            'id': '2',
            'case_name': '密码错误',
            'request_method': 'POST',
            'request_url': 'http://10.1.201.231:8080/ssm_web/user/login',
            'request_params': {'phone': '', 'password': '1234567'},
            'request_headers': {'Content-Type': 'application/json'},
            'request_body': {},
            'description': '拉勾商城登录成功',
            'predict': None,
            'suite_id': 1,
            'projectid': 1,
            'isDeleted': False,
            'status': True,
            'createTime': '2021-11-26 22:30:59',
            'lastUpdateTime': 'None'
        }
    ]
    # excel_util.export_data(case_data)

    result = excel_util.import_case(file=r"C:\Users\wind\PycharmProjects\taitan_interface_platform\测试用例.xls")
    result = json.loads(result)
    print(result)
    result = excel_util.foramt_data(result)
    print(result)