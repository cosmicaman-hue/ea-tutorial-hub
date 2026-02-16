"""
Configuration Constants for Project EA
Centralizes all magic numbers and configuration values
"""

from datetime import timedelta

# ============================================================================
# VETO AND LEADERSHIP QUOTAS
# ============================================================================

# Veto quotas by leadership role
VETO_QUOTAS = {
    'LEADER': 5,
    'CO-LEADER': 3,
    'LEADER OF OPPOSITION': 2,
    'CR': 2,  # Class Representative
    'DEFAULT': 0
}

# Leadership role tenure (in months)
ROLE_TENURE = {
    'DEFAULT': 1,
    'LEADER': 2,
    'LEADER_OF_OPPOSITION': 2,
    'EXTENDED': 1  # Extension period
}

# ============================================================================
# SCORING SYSTEM
# ============================================================================

# Score calculation weights
SCORING_WEIGHTS = {
    'POINTS_PER_STAR': 10,  # 1 star = 10 points
    'POINTS_PER_VETO': 5,   # 1 veto = 5 points
    'POINTS_MULTIPLIER': 1  # Direct points multiplier
}

# Score validation ranges
SCORE_LIMITS = {
    'MIN_POINTS': 0,
    'MAX_POINTS': 1000,
    'MIN_STARS': 0,
    'MAX_STARS': 100,
    'MIN_VETOS': 0,
    'MAX_VETOS': 50
}

# ============================================================================
# AUTHENTICATION AND SECURITY
# ============================================================================

# Password requirements
PASSWORD_REQUIREMENTS = {
    'MIN_LENGTH': 6,
    'MAX_LENGTH': 128,
    'REQUIRE_UPPERCASE': False,
    'REQUIRE_LOWERCASE': False,
    'REQUIRE_DIGIT': False,
    'REQUIRE_SPECIAL': False
}

# Session configuration
SESSION_CONFIG = {
    'LIFETIME': timedelta(hours=8),  # Session expires after 8 hours
    'PERMANENT': True,
    'REFRESH_EACH_REQUEST': True
}

# Rate limiting
RATE_LIMITS = {
    'LOGIN': "10 per minute",
    'REGISTER': "5 per hour",
    'PASSWORD_CHANGE': "3 per hour",
    'SYNC': "100 per hour",
    'DEFAULT': "200 per day, 50 per hour"
}

# Sync key requirements
SYNC_CONFIG = {
    'MIN_KEY_LENGTH': 16,
    'REQUIRED': False  # Set to True to require sync key
}

# ============================================================================
# FILE UPLOAD LIMITS
# ============================================================================

FILE_UPLOAD = {
    'MAX_SIZE_MB': 50,
    'MAX_SIZE_BYTES': 52428800,  # 50 MB
    'ALLOWED_EXTENSIONS': ['.xlsx', '.xls', '.xlsm'],
    'ALLOWED_MIMETYPES': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.ms-excel.sheet.macroEnabled.12',  # .xlsm
        'application/octet-stream'  # Generic binary
    ]
}

# ============================================================================
# VALIDATION CONSTRAINTS
# ============================================================================

# Student profile field limits
PROFILE_LIMITS = {
    'FIRST_NAME_MIN': 2,
    'FIRST_NAME_MAX': 50,
    'SECOND_NAME_MIN': 2,
    'SECOND_NAME_MAX': 50,
    'THIRD_NAME_MAX': 50,
    'ROLL_NUMBER_MAX': 20,
    'CONTACT_NUMBER_LENGTH': 10,
    'PIN_CODE_LENGTH': 6,
    'AADHAR_LENGTH': 12,
    'EMAIL_MAX': 100,
    'NOTES_MAX': 500,
    'MIN_AGE': 5,
    'MAX_AGE': 25
}

# Valid genders
VALID_GENDERS = ['Male', 'Female', 'Other']

# Valid leadership statuses
VALID_LEADERSHIP_STATUSES = ['active', 'suspended', 'vacant']

# ============================================================================
# PARTY SYSTEM
# ============================================================================

# Default parties (id, code, name, voting power)
DEFAULT_PARTIES = [
    {'id': 1, 'code': 'MAP', 'name': 'Muslim Awami Party', 'power': 15},
    {'id': 2, 'code': 'BWP', 'name': 'Bharat Workers Party', 'power': 27},
    {'id': 3, 'code': 'ESP', 'name': 'Eagle Samajwadi Party', 'power': 30},
    {'id': 4, 'code': 'MRP', 'name': 'Muslim Republican Party', 'power': 23},
    {'id': 5, 'code': 'SSP', 'name': 'Saffron Socialist Party', 'power': 57},
    {'id': 6, 'code': 'NJP', 'name': 'National Justice Party', 'power': 15}
]

# Party validation limits
PARTY_LIMITS = {
    'MIN_POWER': 0,
    'MAX_POWER': 1000,
    'MAX_CODE_LENGTH': 10,
    'MAX_NAME_LENGTH': 100
}

# ============================================================================
# LEADERSHIP POSTS
# ============================================================================

# Default leadership posts (id, post, holder, status, veto quota, tenure)
DEFAULT_LEADERSHIP = [
    {'id': 1, 'post': 'LEADER', 'holder': None, 'status': 'vacant', 'vetoQuota': 5, 'tenureMonths': 2},
    {'id': 2, 'post': 'LEADER OF OPPOSITION', 'holder': None, 'status': 'vacant', 'vetoQuota': 2, 'tenureMonths': 2},
    {'id': 3, 'post': 'CO-LEADER', 'holder': None, 'status': 'vacant', 'vetoQuota': 3, 'tenureMonths': 1},
    {'id': 4, 'post': 'CITC', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 5, 'post': 'DWI', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 6, 'post': 'RM', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 7, 'post': 'SC', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 8, 'post': 'ECS', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 9, 'post': 'CCAI', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 10, 'post': 'CI', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 11, 'post': 'ECJ', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1},
    {'id': 12, 'post': 'WCI', 'holder': None, 'status': 'vacant', 'vetoQuota': 0, 'tenureMonths': 1}
]

# Leadership validation limits
LEADERSHIP_LIMITS = {
    'MIN_VETO_QUOTA': 0,
    'MAX_VETO_QUOTA': 20,
    'MAX_POST_NAME_LENGTH': 100,
    'MAX_HOLDER_NAME_LENGTH': 100
}

# ============================================================================
# DATE AND TIME
# ============================================================================

# Timezone
DEFAULT_TIMEZONE = 'Asia/Kolkata'

# Academic year configuration
ACADEMIC_YEAR = {
    'START_MONTH': 4,  # April
    'END_MONTH': 3,    # March
    'MIN_YEAR': 2000,
    'MAX_FUTURE_YEARS': 1  # Allow dates up to 1 year in future
}

# Date validation
DATE_LIMITS = {
    'MIN_YEAR': 2000,
    'MAX_DAYS_IN_PAST': 365,  # Can record points up to 1 year back
    'MAX_DAYS_IN_FUTURE': 0   # Cannot record future dates
}

# ============================================================================
# PAGINATION AND QUERY LIMITS
# ============================================================================

PAGINATION = {
    'DEFAULT_PER_PAGE': 50,
    'MAX_PER_PAGE': 200,
    'MAX_SEARCH_RESULTS': 1000
}

# ============================================================================
# LOGGING AND MONITORING
# ============================================================================

LOGGING = {
    'SLOW_QUERY_THRESHOLD_MS': 2000,  # Log queries slower than 2 seconds
    'LOG_LEVEL_DEV': 'DEBUG',
    'LOG_LEVEL_PROD': 'INFO',
    'LOG_RETENTION_DAYS': 90
}

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHE_CONFIG = {
    'LEADERBOARD_TTL': 3600,  # Cache leaderboard for 1 hour (seconds)
    'PARTY_DATA_TTL': 86400,  # Cache party data for 24 hours
    'STUDENT_PROFILE_TTL': 1800  # Cache student profiles for 30 minutes
}

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_MESSAGES = {
    'GENERIC': 'An error occurred. Please try again or contact support.',
    'UNAUTHORIZED': 'You do not have permission to perform this action.',
    'NOT_FOUND': 'The requested resource was not found.',
    'INVALID_DATA': 'The provided data is invalid.',
    'DUPLICATE_ENTRY': 'This record already exists.',
    'VALIDATION_FAILED': 'Validation failed. Please check your input.',
    'DATABASE_ERROR': 'A database error occurred. Please try again later.',
    'FILE_TOO_LARGE': 'File size exceeds the maximum allowed limit.',
    'INVALID_FILE_TYPE': 'Invalid file type. Please upload a valid file.',
}

# ============================================================================
# FEATURE FLAGS
# ============================================================================

FEATURES = {
    'AUTO_STUDENT_CREATION': False,  # Disable auto-creation for security
    'STUDENT_SELF_REGISTRATION': True,
    'EMAIL_VERIFICATION': False,
    'TWO_FACTOR_AUTH': False,
    'OFFLINE_SYNC': True,
    'PEER_REPLICATION': True,
    'ACTIVITY_LOGGING': True,
    'AUDIT_TRAIL': True
}
