"""
Compute API endpoints for task execution and performance tracking.

This API provides endpoints for demonstrating sequential vs concurrent processing
using Rust-powered Mandelbrot set rendering. Useful for teaching parallel computing concepts.

Endpoints:
    GET /api/compute/health - Check if Rust compute module is available
    GET /api/compute/sequential - Execute sequential tile rendering
    GET /api/compute/concurrent - Execute concurrent tile rendering with multiple threads
"""

from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource

try:
    from model.compute import get_concurrent, get_sequential, is_rustism_available

    HAS_COMPUTE_MODEL = True
except ImportError as e:
    print(f"Warning: Compute model not available: {e}")
    HAS_COMPUTE_MODEL = False

compute_api = Blueprint("compute_api", __name__, url_prefix="/api/compute")
api = Api(compute_api)


class ComputeAPI:
    """
    API endpoints for compute operations using Rust backend.

    These endpoints demonstrate the performance differences between sequential
    and concurrent processing for computationally intensive tasks.
    """

    class _Health(Resource):
        """
        Health check endpoint for Rust compute module.

        Returns:
            JSON with module availability status
        """

        def get(self):
            if not HAS_COMPUTE_MODEL:
                return {
                    "rustism_available": False,
                    "status": "error",
                    "message": "Compute model module not found",
                }, 503

            available = is_rustism_available()
            return {
                "rustism_available": available,
                "status": "ok" if available else "unavailable",
                "message": "Rust compute module is ready"
                if available
                else "Rustism module not loaded",
            }

    class _Sequential(Resource):
        """
        Sequential task execution endpoint.

        Executes Mandelbrot set tile rendering sequentially (one tile at a time)
        to demonstrate baseline performance.

        Query Parameters:
            width (int): Image width in pixels (default: 800)
            height (int): Image height in pixels (default: 600)
            tile_w (int): Tile width (default: 64)
            tile_h (int): Tile height (default: 64)
            max_iter (int): Maximum iterations for Mandelbrot (default: 256)
            time_limit_ms (int): Time limit in milliseconds (default: 2000)

        Returns:
            JSON with task records and performance metrics

        Example:
            GET /api/compute/sequential?width=400&height=300&max_iter=128
        """

        def get(self):
            if not HAS_COMPUTE_MODEL:
                return {
                    "success": False,
                    "error": "Compute model not available",
                    "message": "Model module is not installed or failed to load",
                }, 503

            try:
                # Parse query parameters with defaults
                width = request.args.get("width", default=800, type=int)
                height = request.args.get("height", default=600, type=int)
                tile_w = request.args.get("tile_w", default=64, type=int)
                tile_h = request.args.get("tile_h", default=64, type=int)
                max_iter = request.args.get("max_iter", default=256, type=int)
                time_limit_ms = request.args.get(
                    "time_limit_ms", default=2000, type=int
                )

                # Validate parameters
                if width <= 0 or height <= 0:
                    return {
                        "success": False,
                        "error": "Width and height must be positive",
                    }, 400
                if tile_w <= 0 or tile_h <= 0:
                    return {
                        "success": False,
                        "error": "Tile dimensions must be positive",
                    }, 400
                if max_iter <= 0:
                    return {"success": False, "error": "max_iter must be positive"}, 400

                # Call model layer
                data = get_sequential(
                    width=width,
                    height=height,
                    tile_w=tile_w,
                    tile_h=tile_h,
                    max_iter=max_iter,
                    time_limit_ms=time_limit_ms,
                )

                return {
                    "success": True,
                    "data": data,
                    "params": {
                        "width": width,
                        "height": height,
                        "tile_w": tile_w,
                        "tile_h": tile_h,
                        "max_iter": max_iter,
                        "time_limit_ms": time_limit_ms,
                        "mode": "sequential",
                    },
                    "message": "Sequential tasks executed successfully",
                }
            except RuntimeError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Rustism module not available",
                }, 503
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Error executing sequential tasks",
                }, 500

    class _Concurrent(Resource):
        """
        Concurrent task execution endpoint.

        Executes Mandelbrot set tile rendering concurrently using multiple threads
        to demonstrate performance improvements from parallelization.

        Query Parameters:
            width (int): Image width in pixels (default: 800)
            height (int): Image height in pixels (default: 600)
            tile_w (int): Tile width (default: 64)
            tile_h (int): Tile height (default: 64)
            max_iter (int): Maximum iterations for Mandelbrot (default: 256)
            time_limit_ms (int): Time limit in milliseconds (default: 2000)
            num_threads (int): Number of threads to use (default: 4)

        Returns:
            JSON with task records and performance metrics

        Example:
            GET /api/compute/concurrent?num_threads=8&max_iter=128
        """

        def get(self):
            if not HAS_COMPUTE_MODEL:
                return {
                    "success": False,
                    "error": "Compute model not available",
                    "message": "Model module is not installed or failed to load",
                }, 503

            try:
                # Parse query parameters with defaults
                width = request.args.get("width", default=800, type=int)
                height = request.args.get("height", default=600, type=int)
                tile_w = request.args.get("tile_w", default=64, type=int)
                tile_h = request.args.get("tile_h", default=64, type=int)
                max_iter = request.args.get("max_iter", default=256, type=int)
                time_limit_ms = request.args.get(
                    "time_limit_ms", default=2000, type=int
                )
                num_threads = request.args.get("num_threads", default=4, type=int)

                # Validate parameters
                if width <= 0 or height <= 0:
                    return {
                        "success": False,
                        "error": "Width and height must be positive",
                    }, 400
                if tile_w <= 0 or tile_h <= 0:
                    return {
                        "success": False,
                        "error": "Tile dimensions must be positive",
                    }, 400
                if max_iter <= 0:
                    return {"success": False, "error": "max_iter must be positive"}, 400
                if num_threads <= 0:
                    return {
                        "success": False,
                        "error": "num_threads must be positive",
                    }, 400

                # Call model layer
                data = get_concurrent(
                    width=width,
                    height=height,
                    tile_w=tile_w,
                    tile_h=tile_h,
                    max_iter=max_iter,
                    time_limit_ms=time_limit_ms,
                    num_threads=num_threads,
                )

                return {
                    "success": True,
                    "data": data,
                    "params": {
                        "width": width,
                        "height": height,
                        "tile_w": tile_w,
                        "tile_h": tile_h,
                        "max_iter": max_iter,
                        "time_limit_ms": time_limit_ms,
                        "num_threads": num_threads,
                        "mode": "concurrent",
                    },
                    "message": "Concurrent tasks executed successfully",
                }
            except RuntimeError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Rustism module not available",
                }, 503
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Error executing concurrent tasks",
                }, 500


# Register the endpoints
api.add_resource(ComputeAPI._Health, "/health")
api.add_resource(ComputeAPI._Sequential, "/sequential")
api.add_resource(ComputeAPI._Concurrent, "/concurrent")
