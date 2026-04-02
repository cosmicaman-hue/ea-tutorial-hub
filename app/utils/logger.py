#!/usr/bin/env python3
"""
Comprehensive Logging System
Provides structured logging with security, audit trails, and performance monitoring.
"""
import logging
import logging.handlers
import json
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g, has_request_context
from flask_login import current_user


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if has_request_context():
            log_entry.update({
                'request_id': getattr(g, 'request_id', None),
                'method': request.method,
                'url': request.url,
                'user_agent': request.headers.get('User-Agent', ''),
                'ip': request.remote_addr
            })
            
            # Add user context if authenticated
            try:
                if current_user.is_authenticated:
                    log_entry['user'] = {
                        'id': current_user.id,
                        'login_id': current_user.login_id,
                        'role': current_user.role
                    }
            except:
                pass
        
        # Add exception details if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 'funcName', 
                          'created', 'msecs', 'relativeCreated', 'thread', 
                          'threadName', 'processName', 'process', 'getMessage', 
                          'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self, name: str = 'security'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler('instance/logs/security.log')
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
    
    def log_login_attempt(self, login_id: str, success: bool, ip: str, 
                         user_agent: str = '', reason: str = ''):
        """Log login attempts"""
        self.logger.info(
            "Login attempt",
            extra={
                'event_type': 'login_attempt',
                'login_id': login_id,
                'success': success,
                'ip': ip,
                'user_agent': user_agent,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_permission_check(self, user_id: int, resource: str, 
                           action: str, granted: bool):
        """Log permission checks"""
        self.logger.info(
            "Permission check",
            extra={
                'event_type': 'permission_check',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'granted': granted,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_data_access(self, user_id: int, resource: str, 
                       action: str, record_id: Optional[str] = None):
        """Log data access events"""
        self.logger.info(
            "Data access",
            extra={
                'event_type': 'data_access',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'record_id': record_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_suspicious_activity(self, description: str, severity: str = 'medium',
                              details: Optional[Dict] = None):
        """Log suspicious activities"""
        self.logger.warning(
            f"Suspicious activity: {description}",
            extra={
                'event_type': 'suspicious_activity',
                'severity': severity,
                'description': description,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }
        )


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, name: str = 'performance'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler('instance/logs/performance.log')
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
    
    def log_slow_query(self, query: str, duration: float, 
                      parameters: Optional[Dict] = None):
        """Log slow database queries"""
        self.logger.warning(
            f"Slow query detected: {duration:.2f}s",
            extra={
                'event_type': 'slow_query',
                'query': query[:500],  # Truncate long queries
                'duration': duration,
                'parameters': parameters or {},
                'threshold': 1.0  # 1 second threshold
            }
        )
    
    def log_api_performance(self, endpoint: str, method: str, 
                           status_code: int, duration: float):
        """Log API performance metrics"""
        level = logging.WARNING if duration > 5.0 else logging.INFO
        self.logger.log(
            level,
            f"API call: {method} {endpoint} - {status_code} in {duration:.2f}s",
            extra={
                'event_type': 'api_performance',
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'duration': duration
            }
        )


class AuditLogger:
    """Logger for audit trails"""
    
    def __init__(self, name: str = 'audit'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler('instance/logs/audit.log')
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
    
    def log_user_action(self, user_id: int, action: str, details: Dict):
        """Log user actions for audit trail"""
        self.logger.info(
            f"User action: {action}",
            extra={
                'event_type': 'user_action',
                'user_id': user_id,
                'action': action,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_data_change(self, user_id: int, table: str, record_id: str,
                       old_values: Dict, new_values: Dict):
        """Log data changes"""
        self.logger.info(
            f"Data change in {table}",
            extra={
                'event_type': 'data_change',
                'user_id': user_id,
                'table': table,
                'record_id': record_id,
                'old_values': old_values,
                'new_values': new_values,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_system_event(self, event: str, details: Dict):
        """Log system events"""
        self.logger.info(
            f"System event: {event}",
            extra={
                'event_type': 'system_event',
                'event': event,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        )


def setup_logging(app):
    """Setup comprehensive logging for the Flask app"""
    
    # Create logs directory
    logs_dir = Path('instance/logs')
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    file_handler = logging.handlers.RotatingFileHandler(
        'instance/logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        'instance/logs/errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info("Logging system initialized")
    
    # Log startup
    audit_logger = AuditLogger()
    audit_logger.log_system_event('application_startup', {
        'debug': app.debug,
        'environment': os.getenv('FLASK_ENV', 'production')
    })


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return SecurityLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    return PerformanceLogger()


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()


# Request ID middleware
def generate_request_id():
    """Generate unique request ID"""
    import uuid
    return str(uuid.uuid4())[:8]


def log_request_info():
    """Log request information"""
    if has_request_context():
        g.request_id = generate_request_id()
        
        logger = get_logger('request')
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'event_type': 'request_start',
                'request_id': g.request_id,
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8'),
                'content_length': request.content_length
            }
        )


def log_response_info(response):
    """Log response information"""
    if has_request_context():
        logger = get_logger('request')
        logger.info(
            f"Request completed: {response.status_code}",
            extra={
                'event_type': 'request_end',
                'request_id': getattr(g, 'request_id', None),
                'status_code': response.status_code,
                'content_length': response.content_length
            }
        )
    return response


if __name__ == '__main__':
    # Test logging system
    setup_logging(type('MockApp', (), {'debug': True})())
    
    # Test different loggers
    security_logger = get_security_logger()
    security_logger.log_login_attempt('test_user', True, '127.0.0.1')
    
    performance_logger = get_performance_logger()
    performance_logger.log_slow_query('SELECT * FROM users', 2.5)
    
    audit_logger = get_audit_logger()
    audit_logger.log_user_action(1, 'test_action', {'detail': 'test'})
    
    print("✓ Logging system test completed")
