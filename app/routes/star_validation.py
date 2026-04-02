#!/usr/bin/env python3
"""
Star Validation Routes
Provides endpoints for validating and managing star entries with unified calculation.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.star_calculator import get_star_calculator
from datetime import datetime

star_bp = Blueprint('stars', __name__, url_prefix='/api/stars')


@star_bp.route('/validate', methods=['POST'])
@login_required
def validate_star_entry():
    """Validate a star entry before accepting it"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        stars = data.get('stars')
        month_key = data.get('month_key')
        
        if not student_id or stars is None or not month_key:
            return jsonify({'success': False, 'error': 'student_id, stars, and month_key are required'}), 400
        
        try:
            student_id = int(student_id)
            stars = int(stars)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'student_id and stars must be integers'}), 400
        
        calculator = get_star_calculator()
        valid, message = calculator.validate_star_entry(student_id, stars, month_key)
        
        return jsonify({
            'success': True,
            'valid': valid,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@star_bp.route('/available/<int:student_id>/<month_key>', methods=['GET'])
@login_required
def get_available_stars(student_id, month_key):
    """Get available stars for a student in a given month"""
    try:
        calculator = get_star_calculator()
        
        summary = calculator.get_student_summary(student_id, month_key)
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@star_bp.route('/summary/<int:student_id>/<month_key>', methods=['GET'])
@login_required
def get_star_summary(student_id, month_key):
    """Get complete star summary for a student in a month"""
    try:
        calculator = get_star_calculator()
        
        summary = calculator.get_student_summary(student_id, month_key)
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@star_bp.route('/bonus/<int:student_id>/<date>/<month_key>', methods=['GET'])
@login_required
def get_star_bonus(student_id, date, month_key):
    """Calculate star bonus for a specific date"""
    try:
        calculator = get_star_calculator()
        
        bonus = calculator.get_star_bonus(student_id, date, month_key)
        
        return jsonify({
            'success': True,
            'data': {
                'student_id': student_id,
                'date': date,
                'month': month_key,
                'bonus': bonus,
                'formula': '+100 per normal star use if day score >= -50'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@star_bp.route('/limits', methods=['GET'])
@login_required
def get_star_limits():
    """Get star system limits and rules"""
    try:
        limits = {
            'daily_award_limit': 100,
            'daily_usage_limit': 100,
            'monthly_award_limit': 500,
            'bonus_per_normal_use': 100,
            'bonus_threshold': -50,
            'rules': [
                'Daily award limit: 100 stars per day',
                'Daily usage limit: 100 stars per day',
                'Monthly award limit: 500 stars per month',
                'Star bonus: +100 per normal star use if day score >= -50',
                'Disciplinary usage: Erases that day\'s awarded score',
                'Star transfers: Limited to 3 per 24 hours'
            ]
        }
        
        return jsonify({
            'success': True,
            'data': limits
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@star_bp.route('/calculation-formula', methods=['GET'])
@login_required
def get_calculation_formula():
    """Get the unified star calculation formula"""
    try:
        formula = {
            'name': 'Unified Star Calculation',
            'formula': 'available_stars = carry_in + awards - usage',
            'components': {
                'carry_in': 'Stars carried over from previous month or global counter',
                'awards': 'Sum of all positive star deltas in current month',
                'usage': 'Sum of absolute values of negative star deltas in current month',
                'available': 'Total stars available for use'
            },
            'example': {
                'carry_in': 10,
                'awards': 50,
                'usage': 20,
                'available': 40,
                'calculation': '10 + 50 - 20 = 40'
            }
        }
        
        return jsonify({
            'success': True,
            'data': formula
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
