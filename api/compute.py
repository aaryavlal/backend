"""
Compute endpoints for task execution and performance tracking (multiprocessing)
Endpoints interface with Rust components under rust/rustism
"""

from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource

from model.compute import get_sequential

compute_api = Blueprint("compute_api", __name__, url_prefix="/api/compute")

api = Api(compute_api)


class ComputeAPI:
    """
    API endpoints for compute operations
    """

    class _Sequential(Resource):
        """
        Endpoint for sequential task execution
        GET: Returns sequential task execution data

        TODO: API docs
        """

        def get(self):
            try:
                data = get_sequential()
                return {
                    "success": True,
                    "data": data,
                    "message": "Sequential tasks executed successfully",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Error executing sequential tasks",
                }, 500


# Register the endpoints
api.add_resource(ComputeAPI._Sequential, "/sequential")
