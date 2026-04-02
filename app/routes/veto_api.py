"""
VETO API Routes - Unified VETO System
Uses single source of truth (veto_tracking) for all operations.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.veto_manager_unified import get_unified_veto_manager
from datetime import datetime

veto_bp = Blueprint('veto', __name__, url_prefix='/api/veto')


@veto_bp.route('/status', methods=['GET'])
@login_required
def get_veto_status():
    """Get VETO system status"""
    try:
        manager = get_unified_veto_manager()
        status = manager.get_system_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/balance/<roll>', methods=['GET'])
@login_required
def get_student_balance(roll):
    """Get VETO balance for a student"""
    try:
        manager = get_unified_veto_manager()
        balance = manager.get_balance(roll)
        
        if not balance:
            return jsonify({'success': False, 'error': f'Student {roll} not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'roll': balance.roll,
                'name': balance.name,
                'individual_vetos': balance.individual_vetos,
                'role_vetos': balance.role_vetos,
                'total_vetos': balance.total_vetos,
                'used_vetos': balance.used_vetos,
                'remaining_vetos': balance.remaining_vetos
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/use', methods=['POST'])
@login_required
def use_veto():
    """Use VETOs with deduction from global counter"""
    try:
        data = request.get_json()
        roll = data.get('roll')
        count = data.get('count', 1)
        reason = data.get('reason', '')
        
        if not roll:
            return jsonify({'success': False, 'error': 'Student roll is required'}), 400
        
        manager = get_unified_veto_manager()
        success, message = manager.use_veto(roll, count, reason)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/restore', methods=['POST'])
@login_required
def restore_veto():
    """Restore VETOs (admin function)"""
    try:
        # Only admins can restore VETOs
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        roll = data.get('roll')
        count = data.get('count', 1)
        reason = data.get('reason', 'admin_restoration')
        
        if not roll:
            return jsonify({'success': False, 'error': 'Student roll is required'}), 400
        
        manager = get_unified_veto_manager()
        success, message = manager.restore_veto(roll, count, reason)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/top-holders', methods=['GET'])
@login_required
def get_top_holders():
    """Get top VETO holders"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Cap at 50
        manager = get_unified_veto_manager()
        holders = manager.get_top_holders(limit)
        return jsonify({'success': True, 'data': holders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/usage', methods=['GET'])
@login_required
def get_recent_usage():
    """Get recent VETO usage log"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)  # Cap at 100
        manager = get_unified_veto_manager()
        usage = manager.get_recent_usage(limit)
        return jsonify({'success': True, 'data': usage})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/initialize', methods=['POST'])
@login_required
def initialize_system():
    """Initialize VETO system (admin only)"""
    try:
        # Only admins can initialize
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        # Import and run the main VETO manager
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent / 'scripts'))
        
        from veto_manager import VetoManager
        manager = VetoManager()
        
        success = manager.complete_veto_setup()
        
        if success:
            # Reload unified manager to pick up changes
            from app.utils.veto_manager_unified import UnifiedVetoManager
            unified_manager = UnifiedVetoManager()
            status = unified_manager.get_system_status()
            return jsonify({
                'success': True,
                'message': 'VETO system initialized successfully',
                'data': status
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to initialize VETO system'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/setup-info', methods=['GET'])
@login_required
def get_setup_info():
    """Get information about VETO setup process"""
    try:
        info = {
            'individual_vetos': {
                'Ayush': 1,
                'Arman': 1,
                'Vishes': 1,
                'Pari': 1,
                'Rashi': 1,
                'Sahil': 3,
                'Sakshi': 1,
                'Reeyansh': 3,
                'Nandani': 1
            },
            'role_veto_quotas': {
                'LEADER': 5,
                'LEADER OF OPPOSITION': 2,
                'CO-LEADER': 3,
                'CR': 2
            },
            'setup_steps': [
                '1. Remove all VETOs from everyone',
                '2. Grant individual VETOs to specific students',
                '3. Add role-grant VETOs to post-holders',
                '4. Harden the VETO system',
                '5. Track usage with deduction from global counter'
            ],
            'usage': 'Run: python scripts/veto_manager.py'
        }
        
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@veto_bp.route('/verify-consistency', methods=['GET'])
@login_required
def verify_consistency():
    """Verify that veto_tracking and students[] are in sync (admin only)"""
    try:
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        manager = get_unified_veto_manager()
        is_consistent, issues = manager.verify_consistency()
        
        return jsonify({
            'success': True,
            'consistent': is_consistent,
            'issues': issues,
            'message': '✓ All systems in sync' if is_consistent else f'❌ Found {len(issues)} inconsistencies'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
