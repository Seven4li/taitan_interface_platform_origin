import datetime

import flask_login
from flask import request
from flask_login import login_required

from backend.app import app
from flask_restful import Resource
from backend.models.test_report_model import TestReportModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_KEY_ERROR
from backend.utils.make_response_utils import make_response


class TestReportController:
    def __init__(self):
        pass

    @classmethod
    def query_report_by_id(cls, id):
        report_detail_data = TestReportModel.query.filter_by(reportId=id).first()
        if report_detail_data is None:
            return []
        return report_detail_data.to_dict()

    @classmethod
    def query_report_by_name(cls, report_name):
        report_search_data = TestReportModel.query.filter(
            TestReportModel.reportName.like(f'%{report_name}%')).all()  # []

        response_list = []
        for report_data in report_search_data:
            report_dictdata = report_data.to_dict()
            report_dictdata.update({"create_time": str(report_dictdata.get("create_time"))})
            if report_dictdata.get("update_time"):
                report_dictdata.update({"update_time": str(report_dictdata.get("update_time"))})
            response_list.append(report_dictdata)
        return response_list

    @classmethod
    def query_list(cls, page=1, size=10):
        all_data = TestReportModel.query \
            .filter() \
            .slice((page - 1) * size, page * size) \
            .all()
        response_list = []
        for report_data in all_data:
            report_dictdata = report_data.to_dict()
            report_dictdata.update({"create_time": str(report_dictdata.get("create_time"))})
            if report_dictdata.get("update_time"):
                report_dictdata.update({"update_time": str(report_dictdata.get("update_time"))})
            response_list.append(report_dictdata)
        return response_list


class TestReportService(Resource):
    decorators = [login_required]

    def get(self):
        if not request.args:
            raise REQ_IS_EMPTY_ERROR()
        if not request.args.get("type"):
            raise REQ_KEY_ERROR()

        action_type = request.args.get("type")
        if action_type == "query_detail":
            if not request.args.get("reportId"):
                raise REQ_KEY_ERROR()
            response_data = TestReportController.query_report_by_id(request.args.get("reportId"))
            if len(response_data) < 1:
                return make_response(status=CodeUtil.SUCCESS, data=response_data)
            response_data.update({"create_time": str(response_data.get("create_time"))})
            if response_data.get("update_time"):
                response_data.update({"update_time": str(response_data.get("update_time"))})
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("reportId"):
                raise REQ_KEY_ERROR()
            response_data = TestReportController.query_report_by_name(request.args.get("reportId"))
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "query_list":
            page = request.args.get("page")
            if page:
                if page.isdigit():
                    page = int(page)
                else:
                    return make_response(status=CodeUtil.SUCCESS, data=[])
            size = request.args.get("size")
            if size:
                if size.isdigit():
                    size = int(size)
                else:
                    return make_response(status=CodeUtil.SUCCESS, data=[])
            response_data = TestReportController.query_list(page, size)
            total_count = len(response_data)
            return make_response(status=CodeUtil.SUCCESS,
                                 data=response_data,
                                 total_count=total_count,
                                 page=page,
                                 size=size)
        return make_response(status=CodeUtil.SUCCESS)
