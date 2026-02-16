"""
Global Error Handler Utilities for EA Tutorial Hub
Provides centralized error handling and logging
"""

import logging
from flask import render_template, request, jsonify, current_app
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the application"""
    
    @staticmethod
    def log_error(error, error_type="error", user_id=None, additional_info=None):
        """
        Log error with context information
        
        Args:
            error: The exception or error object
            error_type: Type of error (error, warning, critical)
            user_id: ID of user if applicable
            additional_info: Additional context information
        """
        error_details = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'user_id': user_id,
            'ip_address': request.remote_addr if request else 'Unknown',
            'endpoint': request.endpoint if request else 'Unknown',
            'method': request.method if request else 'Unknown',
            'additional_info': additional_info
        }
        
        log_message = f"[{error_type.upper()}] {error_details['error_message']} | User: {user_id} | IP: {error_details['ip_address']}"
        
        if error_type == "critical":
            logger.critical(log_message, extra=error_details)
        elif error_type == "warning":
            logger.warning(log_message, extra=error_details)
        else:
            logger.error(log_message, extra=error_details)
        
        return error_details


def _should_return_json(path=None):
    """Determine if a JSON response should be returned based on path or Accept header"""
    try:
        # Check Accept header
        accept_header = request.headers.get('Accept', '')
        if 'application/json' in accept_header:
            return True
        
        # Check path for known JSON-returning endpoints
        json_paths = ['/api/', '/scoreboard/', '/quiz-ai/']
        path_to_check = path or request.path
        return any(path_to_check.startswith(p) for p in json_paths)
    except Exception:
        return False


def register_error_handlers(app):
    """
    Register all error handlers with the Flask application
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def page_not_found(error):
        """Handle 404 errors - page not found"""
        ErrorHandler.log_error(
            error, 
            error_type="warning",
            additional_info=f"Requested URL: {request.url}"
        )
        
        # Return JSON for API calls
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'The requested resource was not found',
                'path': request.path
            }), 404
        
        # Return HTML for web requests
        return render_template('errors/404.html', url=request.url), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors - method not allowed"""
        ErrorHandler.log_error(
            error,
            error_type="warning",
            additional_info=f"Request method {request.method} not allowed on {request.path}"
        )
        
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 405,
                'message': f'The {request.method} method is not allowed for this resource',
                'path': request.path
            }), 405
        
        return render_template('errors/405.html', method=request.method), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 errors - internal server errors"""
        ErrorHandler.log_error(
            error,
            error_type="critical",
            additional_info="Internal server error"
        )
        
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 500,
                'message': 'An internal server error occurred. Please try again later.',
                'path': request.path
            }), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors - forbidden access"""
        ErrorHandler.log_error(
            error,
            error_type="warning",
            additional_info=f"Forbidden access to {request.path}"
        )
        
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': 'You do not have permission to access this resource',
                'path': request.path
            }), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors - bad request"""
        ErrorHandler.log_error(
            error,
            error_type="warning",
            additional_info=f"Bad request to {request.path}"
        )
        
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'The request was invalid or malformed',
                'path': request.path
            }), 400
        
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions"""
        error_message = str(error)
        
        # Log the full exception with stack trace
        ErrorHandler.log_error(
            error,
            error_type="critical",
            additional_info="Unhandled exception"
        )
        
        # Don't expose internal error details to users
        if _should_return_json():
            return jsonify({
                'status': 'error',
                'code': 500,
                'message': 'An unexpected error occurred. Please contact support.',
                'path': request.path
            }), 500
        
        return render_template('errors/500.html'), 500
    
    @app.before_request
    def before_request_logging():
        """Log incoming requests"""
        # Only log important requests (not static files)
        if request.path.startswith('/static'):
            return
        
        logger.debug(
            f"Incoming request: {request.method} {request.path} from {request.remote_addr}"
        )
    
    @app.after_request
    def after_request_logging(response):
        """Log outgoing responses"""
        # Only log important requests (not static files)
        if request.path.startswith('/static'):
            return response
        
        # Log slow requests
        if hasattr(request, '__start_time'):
            elapsed = datetime.utcnow() - request.__start_time
            if elapsed.total_seconds() > 2:  # Log requests taking over 2 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.path} took {elapsed.total_seconds():.2f}s"
                )
        
        return response
    
    logger.info("Global error handlers registered successfully")


def setup_logging(app):
    """
    Configure application-wide logging
    
    Args:
        app: Flask application instance
    """
    
    # Create logger
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Set logging level based on environment
    if app.debug:
        handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    
    logger.addHandler(handler)
    
    # Also configure Flask's logger
    app.logger.addHandler(handler)
    
    logger.info("Logging configured successfully")
