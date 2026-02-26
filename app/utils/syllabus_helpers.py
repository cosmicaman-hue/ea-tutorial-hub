"""
Helper functions for merging syllabus-related data for the offline scoreboard.
"""
import json
import re


def merge_syllabus_catalog_superset(existing_catalog, incoming_catalog, parse_int_safe_func):
    """Merge nested syllabus catalog structure without losing chapters."""
    existing = existing_catalog if isinstance(existing_catalog, dict) else {}
    incoming = incoming_catalog if isinstance(incoming_catalog, dict) else {}
    merged = {
        'seed_version': str(incoming.get('seed_version') or existing.get('seed_version') or '').strip(),
        'sources': [],
        'boards': {}
    }

    source_seen = set()
    for source in (existing.get('sources') or []), (incoming.get('sources') or []):
        if not isinstance(source, list):
            continue
        for item in source:
            try:
                key = json.dumps(item, sort_keys=True, ensure_ascii=False)
            except Exception:
                key = str(item)
            if key in source_seen:
                continue
            source_seen.add(key)
            merged['sources'].append(item)

    existing_boards = existing.get('boards') if isinstance(existing.get('boards'), dict) else {}
    incoming_boards = incoming.get('boards') if isinstance(incoming.get('boards'), dict) else {}
    board_keys = set(existing_boards.keys()) | set(incoming_boards.keys())
    for board in sorted(board_keys):
        ex_board = existing_boards.get(board) if isinstance(existing_boards.get(board), dict) else {}
        in_board = incoming_boards.get(board) if isinstance(incoming_boards.get(board), dict) else {}
        ex_classes = ex_board.get('classes') if isinstance(ex_board.get('classes'), dict) else {}
        in_classes = in_board.get('classes') if isinstance(in_board.get('classes'), dict) else {}
        class_keys = set(ex_classes.keys()) | set(in_classes.keys())
        merged_classes = {}
        for class_key in sorted(class_keys, key=lambda v: (parse_int_safe_func(v, 0), str(v))):
            ex_class = ex_classes.get(class_key) if isinstance(ex_classes.get(class_key), dict) else {}
            in_class = in_classes.get(class_key) if isinstance(in_classes.get(class_key), dict) else {}
            ex_subjects = ex_class.get('subjects') if isinstance(ex_class.get('subjects'), dict) else {}
            in_subjects = in_class.get('subjects') if isinstance(in_class.get('subjects'), dict) else {}
            subject_keys = set(ex_subjects.keys()) | set(in_subjects.keys())
            merged_subjects = {}
            for subject in sorted(subject_keys):
                ex_chapters = ex_subjects.get(subject) if isinstance(ex_subjects.get(subject), list) else []
                in_chapters = in_subjects.get(subject) if isinstance(in_subjects.get(subject), list) else []
                chapter_seen = set()
                merged_chapters = []
                for chapter in ex_chapters + in_chapters:
                    text = str(chapter or '').strip()
                    if not text:
                        continue
                    norm = text.lower()
                    if norm in chapter_seen:
                        continue
                    chapter_seen.add(norm)
                    merged_chapters.append(text)
                if merged_chapters:
                    merged_subjects[str(subject)] = merged_chapters
            merged_classes[str(class_key)] = {'subjects': merged_subjects}
        merged['boards'][str(board)] = {'classes': merged_classes}
    return merged


def merge_syllabus_tracking_superset(existing_rows, incoming_rows, parse_int_safe_func, parse_sync_stamp_func):
    """Merge syllabus tracking rows by chapter key while preserving all conducted dates/sessions."""
    merged = {}

    def _normalize_row(item):
        if not isinstance(item, dict):
            return None, None
        board = str(item.get('board') or '').strip().upper()
        class_level = str(item.get('class_level') or item.get('class') or '').strip()
        subject = str(item.get('subject') or '').strip()
        chapter = str(item.get('chapter') or '').strip()
        key = str(item.get('key') or '').strip()
        if not key:
            key = f'{board}||{class_level}||{subject.lower()}||{chapter.lower()}'
        if not key or not board or not class_level or not subject or not chapter:
            return None, None
        dates = []
        date_seen = set()
        for value in item.get('conducted_dates') or []:
            text = str(value or '').strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', text):
                continue
            if text in date_seen:
                continue
            date_seen.add(text)
            dates.append(text)
        dates.sort()
        sessions_by_date = {}
        for sess in item.get('sessions') or []:
            if not isinstance(sess, dict):
                continue
            date = str(sess.get('date') or '').strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                continue
            normalized_sess = {
                'date': date,
                'attended_student_ids': [
                    sid for sid in {
                        parse_int_safe_func(v, 0) for v in (sess.get('attended_student_ids') or [])
                    } if sid > 0
                ],
                'attended_rolls': sorted({
                    str(v or '').strip().upper() for v in (sess.get('attended_rolls') or []) if str(v or '').strip()
                }),
                'attended_names': sorted({
                    str(v or '').strip() for v in (sess.get('attended_names') or []) if str(v or '').strip()
                }),
                'marked_by': str(sess.get('marked_by') or '').strip(),
                'marked_at': str(sess.get('marked_at') or '').strip()
            }
            prev = sessions_by_date.get(date)
            if not prev:
                sessions_by_date[date] = normalized_sess
            else:
                prev_stamp = parse_sync_stamp_func(prev.get('marked_at'))
                next_stamp = parse_sync_stamp_func(normalized_sess.get('marked_at'))
                if next_stamp >= prev_stamp:
                    sessions_by_date[date] = normalized_sess
        normalized = {
            'id': parse_int_safe_func(item.get('id'), 0),
            'key': key,
            'board': board,
            'class_level': class_level,
            'subject': subject,
            'chapter': chapter,
            'conducted_dates': dates,
            'sessions': [sessions_by_date[k] for k in sorted(sessions_by_date.keys())],
            'updated_at': str(item.get('updated_at') or '').strip(),
            'created_at': str(item.get('created_at') or '').strip()
        }
        return key, normalized

    def _merge_pair(prev, nxt):
        prev_stamp = parse_sync_stamp_func(prev.get('updated_at') or prev.get('created_at'))
        next_stamp = parse_sync_stamp_func(nxt.get('updated_at') or nxt.get('created_at'))
        base = dict(nxt if next_stamp >= prev_stamp else prev)
        other = prev if next_stamp >= prev_stamp else nxt
        date_union = sorted({
            str(v).strip()
            for v in (base.get('conducted_dates') or []) + (other.get('conducted_dates') or [])
            if re.match(r'^\d{4}-\d{2}-\d{2}$', str(v or '').strip())
        })
        sessions_by_date = {}
        for sess in (base.get('sessions') or []) + (other.get('sessions') or []):
            if not isinstance(sess, dict):
                continue
            date = str(sess.get('date') or '').strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                continue
            prev_sess = sessions_by_date.get(date)
            if not prev_sess:
                sessions_by_date[date] = dict(sess)
            else:
                p = parse_sync_stamp_func(prev_sess.get('marked_at'))
                n = parse_sync_stamp_func(sess.get('marked_at'))
                if n >= p:
                    sessions_by_date[date] = dict(sess)
        base['conducted_dates'] = date_union
        base['sessions'] = [sessions_by_date[k] for k in sorted(sessions_by_date.keys())]
        return base

    for source in (existing_rows or []), (incoming_rows or []):
        if not isinstance(source, list):
            continue
        for item in source:
            key, normalized = _normalize_row(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            merged[key] = _merge_pair(prev, normalized)

    return list(merged.values())
