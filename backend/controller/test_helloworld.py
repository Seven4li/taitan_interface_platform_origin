from flask_restful import Resource


class IndexService(Resource):

    def get(self):
        return "<h1>Hello Flask Restful </h1>"
