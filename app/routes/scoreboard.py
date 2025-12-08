from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import StudentProfile, StudentPoints, StudentLeaderboard, MonthlyPointsSummary, User
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import openpyxl
from werkzeug.utils import secure_filename
import os
import json
import re
import tempfile

points_bp = Blueprint('points', __name__, url_prefix='/scoreboard')

DEFAULT_PARTIES = [
    {"id": 1, "code": "MAP", "power": 15},
    {"id": 2, "code": "BWP", "power": 27},
    {"id": 3, "code": "ESP", "power": 30},
    {"id": 4, "code": "MRP", "power": 23},
    {"id": 5, "code": "SSP", "power": 57},
    {"id": 6, "code": "NJP", "power": 15},
]

DEFAULT_LEADERSHIP = [
    {"id": 1, "post": "LEADER (L)", "holder": "HARSH MALLICK"},
    {"id": 2, "post": "LEADER OF OPPOSITION (LoP)", "holder": ""},
    {"id": 3, "post": "CO-LEADER (CoL)", "holder": "REEYANSH LAMA"},
    {"id": 4, "post": "CODING & IT CAPTAIN (CITC)", "holder": "SAMARTH PATEL"},
    {"id": 5, "post": "DISCIPLINE & WELFARE IN-CHARGE (DWI)", "holder": "AANSH MANDAL"},
    {"id": 6, "post": "RESOURCE MANAGER (RM)", "holder": "RIYA SINGH"},
    {"id": 7, "post": "SPORTS CAPTAIN (SC)", "holder": "REEYANSH LAMA"},
    {"id": 8, "post": "ENGLISH CAPTAIN- SENIOR (ECS)", "holder": "ABDUL ARMAN"},
    {"id": 9, "post": "CULTURE & CREATIVE ARTS IN-CHARGE (CCAI)", "holder": "SAKSHI"},
    {"id": 10, "post": "CLEANLINESS IN-CHARGE (CI)", "holder": "SHANKAR PRADHAN"},
    {"id": 11, "post": "ENGLISH CAPTAIN- JUNIOR (ECJ)", "holder": "REHMATUN KHATUN"},
    {"id": 12, "post": "WELCOME & COMMUNICATION IN-CHARGE (WCI)", "holder": "SHOMIYA XALXO"},
    {"id": 13, "post": "LEADER", "holder": ""},
    {"id": 14, "post": "LEADER OF OPPOSITION", "holder": ""},
]


def _politics_file_path():
    return os.path.join(current_app.instance_path, 'scoreboard_politics.json')


def _normalize_parties(parties):
    normalized = []
    for idx, party in enumerate(parties, start=1):
        code = str(party.get('code', '')).strip()
        if not code:
            continue
        try:
            power = int(party.get('power') or 0)
        except (TypeError, ValueError):
            power = 0
        party_id = party.get('id') or idx
        normalized.append({'id': int(party_id), 'code': code, 'power': power})
    return normalized


def _normalize_leadership(posts):
    normalized = []
    for idx, post in enumerate(posts, start=1):
        title = str(post.get('post', '')).strip()
        if not title:
            continue
        holder = str(post.get('holder', '')).strip()
        post_id = post.get('id') or idx
        normalized.append({'id': int(post_id), 'post': title, 'holder': holder})
    return normalized


def _load_politics_data():
    path = _politics_file_path()
    if not os.path.exists(path):
        return {
            'parties': DEFAULT_PARTIES.copy(),
            'leadership': DEFAULT_LEADERSHIP.copy()
        }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['parties'] = _normalize_parties(data.get('parties', []))
        data['leadership'] = _normalize_leadership(data.get('leadership', []))
        return data
    except Exception:
        return {
            'parties': DEFAULT_PARTIES.copy(),
            'leadership': DEFAULT_LEADERSHIP.copy()
        }


def _save_politics_data(data):
    os.makedirs(current_app.instance_path, exist_ok=True)
    payload = {
        'parties': _normalize_parties(data.get('parties', [])),
        'leadership': _normalize_leadership(data.get('leadership', []))
    }
    with open(_politics_file_path(), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def _extract_party_and_leadership(ws):
    parties = []
    leadership = []

    party_row = None
    party_col = None
    power_col = None
    post_row = None
    post_col = None
    holder_col = None

    for row in ws.iter_rows(min_row=1, max_row=50):
        for cell in row:
            if isinstance(cell.value, str):
                label = cell.value.strip().lower()
                if label == 'party':
                    party_row = cell.row
                    party_col = cell.column
                if label == 'power':
                    power_col = cell.column
                if label == 'post':
                    post_row = cell.row
                    post_col = cell.column
                if label == 'post holders':
                    holder_col = cell.column

    if party_row and party_col and power_col:
        for r in range(party_row + 1, party_row + 20):
            code = ws.cell(r, party_col).value
            power = ws.cell(r, power_col).value
            if not code:
                continue
            if str(code).strip().upper() == 'TOTAL':
                continue
            if isinstance(power, (int, float)):
                parties.append({'code': str(code).strip(), 'power': int(power)})

    if post_row and post_col and holder_col:
        for r in range(post_row + 1, post_row + 30):
            post = ws.cell(r, post_col).value
            holder = ws.cell(r, holder_col).value
            if post:
                leadership.append({'post': str(post).strip(), 'holder': str(holder).strip() if holder else ''})

    return parties, leadership


FEB26_SEED = json.loads(r'''
{
  "students": [
    { "id": 1, "roll": "EA24A01", "name": "Ayush Gupta** (CR) (Vv)", "class": 4, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 2, "roll": "EA24A03", "name": "Ayat Parveen", "class": 4, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 3, "roll": "EA24A04", "name": "Tanu Sinha**", "class": 4, "fees": 600, "total_score": 60, "rank": 20, "vote_power": 4 },
    { "id": 4, "roll": "EA24A05", "name": "Rashi (v)", "class": 3, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 5, "roll": "EA25A07", "name": "Vishes Xalxo***(v)", "class": 3, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 6, "roll": "EA25A13", "name": "Afreen Khatun", "class": 3, "fees": 600, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 7, "roll": "EA25A15", "name": "Ansh Kumar Singh", "class": 2, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 8, "roll": "EA24B01", "name": "Pari Gupta****** (v)", "class": 6, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 9, "roll": "EA24B03", "name": "Deep Das*", "class": 6, "fees": 1000, "total_score": 97, "rank": 12, "vote_power": 6 },
    { "id": 10, "roll": "EA24B09", "name": "Abdul Arman**** (ECS) (PP)", "class": 5, "fees": 1000, "total_score": 79, "rank": 16, "vote_power": 5 },
    { "id": 11, "roll": "EA25B05", "name": "Rajveer Thakur", "class": 6, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 12, "roll": "EA25B06", "name": "Jay Arya***", "class": 5, "fees": 800, "total_score": 139, "rank": 6, "vote_power": 8 },
    { "id": 13, "roll": "EA25B10", "name": "Shiva Mallick (v)", "class": 5, "fees": 1000, "total_score": 160, "rank": 3, "vote_power": 9 },
    { "id": 14, "roll": "EA25B13", "name": "Rehmetun Khatun (ECJ)", "class": 6, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 15, "roll": "EA25B14", "name": "Prem Oraon*****", "class": 6, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 16, "roll": "EA24C02", "name": "Sahil Yadav****************** (vvv)", "class": 8, "fees": 0, "total_score": 94, "rank": 13, "vote_power": 6 },
    { "id": 17, "roll": "EA24C03", "name": "Abhik Mallik", "class": 8, "fees": 1000, "total_score": 41, "rank": 25, "vote_power": 3 },
    { "id": 18, "roll": "EA24C06", "name": "Sakshi*** (v) (CCAI)", "class": 8, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 19, "roll": "EA25C07", "name": "Khushi Paswan** (v)", "class": 8, "fees": 500, "total_score": 72, "rank": 17, "vote_power": 4 },
    { "id": 20, "roll": "EA25C09", "name": "Shomiya Xalxo*** (WCI) (PP)", "class": 7, "fees": 1000, "total_score": 182, "rank": 2, "vote_power": 10 },
    { "id": 21, "roll": "EA25C10", "name": "Adarsh Arya*", "class": 8, "fees": 1200, "total_score": 1, "rank": 27, "vote_power": 1 },
    { "id": 22, "roll": "EA25C11", "name": "Sourav Das*", "class": 8, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 23, "roll": "EA25C12", "name": "Shubham Singha (PP)", "class": 8, "fees": 1200, "total_score": 47, "rank": 22, "vote_power": 3 },
    { "id": 24, "roll": "EA25C15", "name": "Nirupam Vaid*", "class": 8, "fees": 1500, "total_score": 35, "rank": 26, "vote_power": 2 },
    { "id": 25, "roll": "EA25C17", "name": "Alen Ghartimagar", "class": 8, "fees": 1500, "total_score": 63, "rank": 19, "vote_power": 4 },
    { "id": 26, "roll": "EA25C18", "name": "N Riya Kumari", "class": 8, "fees": 1500, "total_score": 118, "rank": 9, "vote_power": 7 },
    { "id": 27, "roll": "EA25C19", "name": "Samarth Patel*(CITC)", "class": 8, "fees": 1500, "total_score": 153, "rank": 5, "vote_power": 9 },
    { "id": 28, "roll": "EA25C20", "name": "Rishi Trivedi", "class": 8, "fees": 1500, "total_score": 90, "rank": 15, "vote_power": 5 },
    { "id": 29, "roll": "EA25C21", "name": "Sristi Kumari", "class": 7, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 30, "roll": "EA25C22", "name": "Piyush Rajak", "class": 8, "fees": 1000, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 31, "roll": "EA25C23", "name": "Abhinav Khati (CR) (PP)", "class": 7, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 32, "roll": "EA26C24", "name": "Rishabh Kumar Singh", "class": 7, "fees": 0, "total_score": 42, "rank": 24, "vote_power": 3 },
    { "id": 33, "roll": "EA24D01", "name": "Jay Kumar Yadav*** (CR) (V)", "class": 10, "fees": 0, "total_score": 187, "rank": 1, "vote_power": 10 },
    { "id": 34, "roll": "EA24D06", "name": "Tanmay Biswas*", "class": 10, "fees": 2000, "total_score": 102, "rank": 11, "vote_power": 6 },
    { "id": 35, "roll": "EA24D08", "name": "Sanjana Sutradhar (PP)", "class": 9, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 36, "roll": "EA25D12", "name": "Roshan Paswan** (PP)", "class": 10, "fees": 2000, "total_score": 158, "rank": 4, "vote_power": 9 },
    { "id": 37, "roll": "EA25D13", "name": "Aamna Khatoon*", "class": 10, "fees": 1500, "total_score": 105, "rank": 10, "vote_power": 6 },
    { "id": 38, "roll": "EA24D15", "name": "Reeyansh Lama (VVvvv) (CoL) (SC)", "class": 9, "fees": 1500, "total_score": 122, "rank": 7, "vote_power": 7 },
    { "id": 39, "roll": "EA25D17", "name": "Aditya Singh***", "class": 10, "fees": 2000, "total_score": 57, "rank": 21, "vote_power": 4 },
    { "id": 40, "roll": "EA25D20", "name": "Harsh Mallik****** (VVV) (L)", "class": 9, "fees": 1500, "total_score": 43, "rank": 23, "vote_power": 3 },
    { "id": 41, "roll": "EA25D21", "name": "Xavier Herenj***", "class": 9, "fees": 2000, "total_score": -30, "rank": 46, "vote_power": -1 },
    { "id": 42, "roll": "EA25D22", "name": "Mahek Mahato*******", "class": 9, "fees": 2000, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 43, "roll": "EA25D24", "name": "Aansh Mandal****** (DWI)", "class": 10, "fees": 2000, "total_score": 122, "rank": 7, "vote_power": 7 },
    { "id": 44, "roll": "EA24D25", "name": "Nandani Gupta** (v)", "class": 9, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 45, "roll": "EA25D26", "name": "Shankar Pradhan (CI)", "class": 9, "fees": 2000, "total_score": 92, "rank": 14, "vote_power": 5 },
    { "id": 46, "roll": "EA26D28", "name": "Riya Singh (RM)", "class": 9, "fees": 2000, "total_score": 70, "rank": 18, "vote_power": 4 }
  ],
  "scores": [
    { "id": 1, "studentId": 3, "date": "2026-02-01", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 2, "studentId": 9, "date": "2026-02-01", "points": 97, "month": "2026-02", "notes": "" },
    { "id": 3, "studentId": 10, "date": "2026-02-01", "points": 79, "month": "2026-02", "notes": "" },
    { "id": 4, "studentId": 12, "date": "2026-02-01", "points": 79, "month": "2026-02", "notes": "" },
    { "id": 5, "studentId": 12, "date": "2026-02-02", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 6, "studentId": 13, "date": "2026-02-01", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 7, "studentId": 13, "date": "2026-02-03", "points": 100, "month": "2026-02", "notes": "" },
    { "id": 8, "studentId": 16, "date": "2026-02-01", "points": 94, "month": "2026-02", "notes": "" },
    { "id": 9, "studentId": 17, "date": "2026-02-01", "points": 41, "month": "2026-02", "notes": "" },
    { "id": 10, "studentId": 19, "date": "2026-02-01", "points": 72, "month": "2026-02", "notes": "" },
    { "id": 11, "studentId": 20, "date": "2026-02-01", "points": 182, "month": "2026-02", "notes": "" },
    { "id": 12, "studentId": 21, "date": "2026-02-01", "points": -99, "month": "2026-02", "notes": "" },
    { "id": 13, "studentId": 21, "date": "2026-02-03", "points": 100, "month": "2026-02", "notes": "" },
    { "id": 14, "studentId": 22, "date": "2026-02-01", "points": 0, "month": "2026-02", "notes": "" },
    { "id": 15, "studentId": 23, "date": "2026-02-01", "points": 47, "month": "2026-02", "notes": "" },
    { "id": 16, "studentId": 24, "date": "2026-02-01", "points": 35, "month": "2026-02", "notes": "" },
    { "id": 17, "studentId": 25, "date": "2026-02-01", "points": 63, "month": "2026-02", "notes": "" },
    { "id": 18, "studentId": 26, "date": "2026-02-01", "points": 118, "month": "2026-02", "notes": "" },
    { "id": 19, "studentId": 27, "date": "2026-02-01", "points": 153, "month": "2026-02", "notes": "" },
    { "id": 20, "studentId": 28, "date": "2026-02-01", "points": 90, "month": "2026-02", "notes": "" },
    { "id": 21, "studentId": 32, "date": "2026-02-01", "points": 42, "month": "2026-02", "notes": "" },
    { "id": 22, "studentId": 33, "date": "2026-02-01", "points": 187, "month": "2026-02", "notes": "" },
    { "id": 23, "studentId": 34, "date": "2026-02-01", "points": 102, "month": "2026-02", "notes": "" },
    { "id": 24, "studentId": 36, "date": "2026-02-01", "points": 158, "month": "2026-02", "notes": "" },
    { "id": 25, "studentId": 37, "date": "2026-02-01", "points": 105, "month": "2026-02", "notes": "" },
    { "id": 26, "studentId": 38, "date": "2026-02-01", "points": 122, "month": "2026-02", "notes": "" },
    { "id": 27, "studentId": 39, "date": "2026-02-01", "points": 57, "month": "2026-02", "notes": "" },
    { "id": 28, "studentId": 40, "date": "2026-02-01", "points": 43, "month": "2026-02", "notes": "" },
    { "id": 29, "studentId": 41, "date": "2026-02-01", "points": -30, "month": "2026-02", "notes": "" },
    { "id": 30, "studentId": 43, "date": "2026-02-01", "points": 122, "month": "2026-02", "notes": "" },
    { "id": 31, "studentId": 45, "date": "2026-02-01", "points": 127, "month": "2026-02", "notes": "" },
    { "id": 32, "studentId": 45, "date": "2026-02-02", "points": -35, "month": "2026-02", "notes": "" },
    { "id": 33, "studentId": 46, "date": "2026-02-01", "points": 70, "month": "2026-02", "notes": "" }
  ],
  "parties": [
    { "code": "MAP", "power": 15 },
    { "code": "BWP", "power": 27 },
    { "code": "ESP", "power": 30 },
    { "code": "MRP", "power": 23 },
    { "code": "SSP", "power": 57 },
    { "code": "NJP", "power": 15 }
  ],
  "leadership": [
    { "post": "LEADER (L)", "holder": "HARSH MALLICK" },
    { "post": "LEADER OF OPPOSITION (LoP)", "holder": "" },
    { "post": "CO-LEADER (CoL)", "holder": "REEYANSH LAMA" },
    { "post": "CODING & IT CAPTAIN (CITC)", "holder": "SAMARTH PATEL" },
    { "post": "DISCIPLINE & WELFARE IN-CHARGE (DWI)", "holder": "AANSH MANDAL" },
    { "post": "RESOURCE MANAGER (RM)", "holder": "RIYA SINGH" },
    { "post": "SPORTS CAPTAIN (SC)", "holder": "REEYANSH LAMA" },
    { "post": "ENGLISH CAPTAIN- SENIOR (ECS)", "holder": "ABDUL ARMAN" },
    { "post": "CULTURE & CREATIVE ARTS IN-CHARGE (CCAI)", "holder": "SAKSHI" },
    { "post": "CLEANLINESS IN-CHARGE (CI)", "holder": "SHANKAR PRADHAN" },
    { "post": "ENGLISH CAPTAIN- JUNIOR (ECJ)", "holder": "REHMATUN KHATUN" },
    { "post": "WELCOME & COMMUNICATION IN-CHARGE (WCI)", "holder": "SHOMIYA XALXO" },
    { "post": "LEADER", "holder": "" },
    { "post": "LEADER OF OPPOSITION", "holder": "" }
  ]
}
''')

# ============== ROUTES ==============

@points_bp.route('/offline')
def offline_scoreboard():
    """Serve offline scoreboard HTML"""
    return send_file('static/offline_scoreboard.html')


@points_bp.route('/')
@login_required
def scoreboard_home():
    """Main scoreboard page"""
    return render_template('scoreboard/index.html')


@points_bp.route('/party-data', methods=['GET', 'POST'])
@login_required
def party_data():
    """Get or update party system data"""
    data = _load_politics_data()
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        payload = request.get_json() or {}
        data['parties'] = payload.get('parties', [])
        saved = _save_politics_data(data)
        return jsonify({'success': True, 'parties': saved['parties']})
    return jsonify({'success': True, 'parties': data['parties']})


@points_bp.route('/leadership-data', methods=['GET', 'POST'])
@login_required
def leadership_data():
    """Get or update leadership posts"""
    data = _load_politics_data()
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        payload = request.get_json() or {}
        data['leadership'] = payload.get('leadership', [])
        saved = _save_politics_data(data)
        return jsonify({'success': True, 'leadership': saved['leadership']})
    return jsonify({'success': True, 'leadership': data['leadership']})


@points_bp.route('/data')
@login_required
def get_scoreboard_data():
    """Get scoreboard data with filters"""
    try:
        # Get filters from request
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        class_filter = request.args.get('class', 'All')
        group_filter = request.args.get('group', 'All')
        search = request.args.get('search', '').lower()
        month_key = request.args.get('month')
        
        # Parse dates
        if not date_from or not date_to:
            today = date.today()
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = datetime.fromisoformat(date_from).date()
            date_to = datetime.fromisoformat(date_to).date()
        
        # Query students
        query = StudentProfile.query.all()
        
        # Apply filters
        students_data = []
        for student in query:
            # Class filter
            if class_filter != 'All' and str(student.class_name) != str(class_filter):
                continue
            # Group filter
            if group_filter != 'All' and str(student.group) != str(group_filter):
                continue
            # Search filter
            if search and search not in student.full_name.lower() and search not in student.roll_number.lower():
                continue
            
            # Get points for this student in date range
            points_records = StudentPoints.query.filter(
                StudentPoints.student_id == student.id,
                StudentPoints.date_recorded >= date_from,
                StudentPoints.date_recorded <= date_to
            ).all()
            
            total_points = sum(p.points for p in points_records)
            total_stars = sum(p.stars for p in points_records)
            total_vetos = sum(p.vetos for p in points_records)
            
            # Create daily breakdown
            daily_data = {}
            for record in points_records:
                date_key = record.date_recorded.isoformat()
                daily_data[date_key] = {
                    'points': record.points,
                    'stars': record.stars,
                    'vetos': record.vetos,
                    'notes': record.notes
                }
            
            profile_data = student.profile_data or {}
            students_data.append({
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'fees': profile_data.get('fees'),
                'vote_power': profile_data.get('vote_power'),
                'sheet_total_score': profile_data.get('total_score'),
                'sheet_rank': profile_data.get('rank'),
                'total_points': total_points,
                'total_stars': total_stars,
                'total_vetos': total_vetos,
                'daily_data': daily_data,
                'net_score': total_points + (total_stars * 10) - (total_vetos * 5)
            })
        
        # Sort by net score descending
        students_data.sort(key=lambda x: x['net_score'], reverse=True)
        
        # Add ranks
        for idx, student in enumerate(students_data, 1):
            student['rank'] = idx
        
        # Get date columns for table headers
        date_range = []
        current = date_from
        while current <= date_to:
            date_range.append(current.isoformat())
            current += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'students': students_data,
            'date_range': date_range,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_scoreboard_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/add-points', methods=['POST'])
@login_required
def add_points():
    """Add points for a student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        date_recorded = datetime.fromisoformat(data.get('date')).date()
        points = int(data.get('points', 0))
        stars = int(data.get('stars', 0))
        vetos = int(data.get('vetos', 0))
        notes = data.get('notes', '')
        
        # Check if record exists
        record = StudentPoints.query.filter_by(
            student_id=student_id,
            date_recorded=date_recorded
        ).first()
        
        if record:
            # Update existing
            record.points = points
            record.stars = stars
            record.vetos = vetos
            record.notes = notes
            record.recorded_by = current_user.username
        else:
            # Create new
            record = StudentPoints(
                student_id=student_id,
                date_recorded=date_recorded,
                points=points,
                stars=stars,
                vetos=vetos,
                notes=notes,
                recorded_by=current_user.username
            )
            db.session.add(record)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Points added successfully',
            'data': record.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in add_points: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/add-student', methods=['POST'])
@login_required
def add_student():
    """Add a new student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        
        # Check if student already exists
        existing = StudentProfile.query.filter_by(roll_number=data.get('roll_number')).first()
        if existing:
            return jsonify({'success': False, 'error': 'Student with this roll number already exists'}), 400
        
        student = StudentProfile(
            roll_number=data.get('roll_number'),
            full_name=data.get('full_name'),
            class_name=data.get('class'),
            group=data.get('group', 'A'),
            user_id=None  # Not linked to user account
        )

        profile_data = student.profile_data or {}
        if data.get('fees') is not None:
            profile_data['fees'] = data.get('fees')
        if data.get('vote_power') is not None:
            profile_data['vote_power'] = data.get('vote_power')
        student.profile_data = profile_data
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Student added successfully',
            'student': {
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'fees': profile_data.get('fees'),
                'vote_power': profile_data.get('vote_power')
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in add_student: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/delete-student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """Delete a student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_student: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/update-profile/<int:student_id>', methods=['POST'])
@login_required
def update_profile(student_id):
    """Update student profile with extended fields"""
    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        data = request.get_json()
        
        # Update basic fields
        if 'full_name' in data:
            student.full_name = data['full_name']
        if 'class' in data:
            student.class_name = data['class']
        if 'group' in data:
            student.group = data['group']
        
        # Update extended profile fields
        if not student.profile_data:
            student.profile_data = {}
        
        profile_updates = {
            'fatherName', 'motherName', 'dateOfBirth', 'bloodGroup', 'aadhar',
            'phone', 'email', 'address', 'parentPhone', 'admissionDate', 'academicYear',
            'fees', 'vote_power', 'total_score', 'rank'
        }
        
        for field in profile_updates:
            if field in data:
                student.profile_data[field] = data[field]
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'student': {
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'profile_data': student.profile_data
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in update_profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/import-excel', methods=['POST'])
@login_required
def import_excel():
    """Import student data and scores from Excel file"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            return jsonify({'success': False, 'error': 'Only Excel files (.xlsx, .xls, .xlsm) are supported'}), 400
        
        # Save and process file
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Load workbook
        wb = openpyxl.load_workbook(temp_path, data_only=True)
        sheet_name = request.form.get('sheet') or request.args.get('sheet')
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        
        imported_count = 0
        errors = []
        
        header_row = [cell.value for cell in ws[1]]
        header_map = {}
        for idx, value in enumerate(header_row, start=1):
            if isinstance(value, str):
                header_map[value.strip().lower()] = idx

        def find_header(candidates):
            for key in candidates:
                for header, idx in header_map.items():
                    if key in header:
                        return idx
            return None

        roll_col = find_header(['roll'])
        name_col = find_header(['student name', 'name'])
        class_col = find_header(['class'])
        fees_col = find_header(['fees'])
        total_col = find_header(['total score'])
        rank_col = find_header(['rank'])
        vote_col = find_header(['vote power', 'votepower'])

        if not roll_col or not name_col:
            return jsonify({'success': False, 'error': 'Missing roll or student name column'}), 400

        date_columns = []
        for idx, header in enumerate(header_row, start=1):
            if isinstance(header, (datetime, date)):
                date_columns.append((idx, header.date()))
            elif isinstance(header, str):
                try:
                    parsed = datetime.fromisoformat(header.strip())
                    date_columns.append((idx, parsed.date()))
                except (ValueError, TypeError):
                    pass
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            try:
                roll_number = ws.cell(row_idx, roll_col).value
                full_name = ws.cell(row_idx, name_col).value
                class_name = ws.cell(row_idx, class_col).value if class_col else 'Unknown'
                fees_value = ws.cell(row_idx, fees_col).value if fees_col else None
                total_value = ws.cell(row_idx, total_col).value if total_col else None
                rank_value = ws.cell(row_idx, rank_col).value if rank_col else None
                vote_value = ws.cell(row_idx, vote_col).value if vote_col else None
                
                if not roll_number or not full_name:
                    continue

                roll_str = str(roll_number).strip()
                group_match = re.search(r'^EA\\d{2}([A-Z])', roll_str)
                group = group_match.group(1) if group_match else 'A'

                # Get or create student
                student = StudentProfile.query.filter_by(roll_number=roll_str).first()
                if not student:
                    student = StudentProfile(
                        roll_number=roll_str,
                        full_name=str(full_name),
                        class_name=str(class_name),
                        group=group
                    )
                    db.session.add(student)
                    db.session.flush()
                else:
                    student.full_name = str(full_name)
                    student.class_name = str(class_name)
                    student.group = group

                profile_data = student.profile_data or {}
                if isinstance(fees_value, (int, float)):
                    profile_data['fees'] = int(fees_value)
                if isinstance(vote_value, (int, float)):
                    profile_data['vote_power'] = int(vote_value)
                if isinstance(total_value, (int, float)):
                    profile_data['total_score'] = int(total_value)
                if isinstance(rank_value, (int, float)):
                    profile_data['rank'] = int(rank_value)
                student.profile_data = profile_data
                
                # Process date columns (scores)
                for col_idx, date_recorded in date_columns:
                    score_value = ws.cell(row_idx, col_idx).value
                    if score_value is None or score_value == '':
                        continue
                    if not isinstance(score_value, (int, float)):
                        continue

                    record = StudentPoints.query.filter_by(
                        student_id=student.id,
                        date_recorded=date_recorded
                    ).first()

                    if record:
                        record.points = int(score_value)
                        record.recorded_by = current_user.username
                    else:
                        record = StudentPoints(
                            student_id=student.id,
                            date_recorded=date_recorded,
                            points=int(score_value),
                            recorded_by=current_user.username
                        )
                        db.session.add(record)
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")

        # Extract party and leadership data if present
        parties, leadership = _extract_party_and_leadership(ws)
        if parties or leadership:
            _save_politics_data({
                'parties': parties or DEFAULT_PARTIES,
                'leadership': leadership or DEFAULT_LEADERSHIP
            })

        db.session.commit()
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'message': f'Imported {imported_count} records successfully',
            'imported_count': imported_count,
            'errors': errors
        })
    except Exception as e:
        current_app.logger.error(f"Error in import_excel: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/seed-feb26', methods=['POST'])
@login_required
def seed_feb26():
    """Seed database with Feb 26 sheet data"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    mode = request.args.get('mode', 'replace_unlinked')
    try:
        rolls = {s['roll'] for s in FEB26_SEED['students']}

        if mode == 'replace_unlinked':
            StudentProfile.query.filter(
                StudentProfile.user_id.is_(None),
                StudentProfile.roll_number.notin_(list(rolls))
            ).delete(synchronize_session=False)

        # Upsert students
        for student_data in FEB26_SEED['students']:
            roll = student_data['roll']
            student = StudentProfile.query.filter_by(roll_number=roll).first()
            group_match = re.search(r'^EA\\d{2}([A-Z])', roll)
            group = group_match.group(1) if group_match else 'A'
            if not student:
                student = StudentProfile(
                    roll_number=roll,
                    full_name=student_data.get('name'),
                    class_name=str(student_data.get('class')),
                    group=group
                )
                db.session.add(student)
                db.session.flush()
            else:
                student.full_name = student_data.get('name')
                student.class_name = str(student_data.get('class'))
                student.group = group

            profile_data = student.profile_data or {}
            profile_data['fees'] = student_data.get('fees', 0)
            profile_data['vote_power'] = student_data.get('vote_power')
            profile_data['total_score'] = student_data.get('total_score')
            profile_data['rank'] = student_data.get('rank')
            student.profile_data = profile_data

        db.session.flush()

        seed_id_map = {s['id']: s['roll'] for s in FEB26_SEED['students']}
        imported_scores = 0
        for score in FEB26_SEED['scores']:
            roll = seed_id_map.get(score['studentId'])
            if not roll:
                continue
            student = StudentProfile.query.filter_by(roll_number=roll).first()
            if not student:
                continue
            date_recorded = datetime.fromisoformat(score['date']).date()
            record = StudentPoints.query.filter_by(
                student_id=student.id,
                date_recorded=date_recorded
            ).first()
            if record:
                record.points = int(score['points'])
                record.recorded_by = current_user.username
            else:
                record = StudentPoints(
                    student_id=student.id,
                    date_recorded=date_recorded,
                    points=int(score['points']),
                    recorded_by=current_user.username
                )
                db.session.add(record)
            imported_scores += 1

        _save_politics_data({
            'parties': FEB26_SEED.get('parties', DEFAULT_PARTIES),
            'leadership': FEB26_SEED.get('leadership', DEFAULT_LEADERSHIP)
        })

        db.session.commit()
        return jsonify({
            'success': True,
            'students': len(FEB26_SEED['students']),
            'scores': imported_scores
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in seed_feb26: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/leaderboard')
@login_required
def get_leaderboard():
    """Get top students leaderboard"""
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Build query
        leaderboard = db.session.query(
            StudentProfile.id,
            StudentProfile.full_name,
            StudentProfile.class_name,
            db.func.sum(StudentPoints.points).label('total_points'),
            db.func.sum(StudentPoints.stars).label('total_stars'),
            db.func.sum(StudentPoints.vetos).label('total_vetos')
        ).join(
            StudentPoints, StudentProfile.id == StudentPoints.student_id
        ).filter(
            db.extract('month', StudentPoints.date_recorded) == month,
            db.extract('year', StudentPoints.date_recorded) == year
        ).group_by(
            StudentProfile.id,
            StudentProfile.full_name,
            StudentProfile.class_name
        ).order_by(
            (db.func.sum(StudentPoints.points) + 
             db.func.sum(StudentPoints.stars) * 10 - 
             db.func.sum(StudentPoints.vetos) * 5).desc()
        ).limit(limit).all()
        
        result = []
        for idx, record in enumerate(leaderboard, 1):
            net_score = (record.total_points or 0) + ((record.total_stars or 0) * 10) - ((record.total_vetos or 0) * 5)
            result.append({
                'rank': idx,
                'name': record.full_name,
                'class': record.class_name,
                'total_points': record.total_points or 0,
                'total_stars': record.total_stars or 0,
                'total_vetos': record.total_vetos or 0,
                'net_score': net_score
            })
        
        return jsonify({'success': True, 'leaderboard': result})
    except Exception as e:
        current_app.logger.error(f"Error in get_leaderboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/month-summary')
@login_required
def get_month_summary():
    """Get previous months for tab navigation"""
    try:
        today = date.today()
        months_data = []
        
        for i in range(4):  # Current + 3 previous months
            check_date = today - relativedelta(months=i)
            month_key = f"{check_date.year}-{check_date.month:02d}"
            month_name = calendar.month_name[check_date.month]
            
            months_data.append({
                'key': month_key,
                'name': f"{month_name} {check_date.year}",
                'year': check_date.year,
                'month': check_date.month,
                'is_current': i == 0
            })
        
        return jsonify({
            'success': True,
            'months': months_data,
            'current_month': today.month,
            'current_year': today.year,
            'today': today.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_month_summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

