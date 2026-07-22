import copy


def payload_for_external_replication(payload):
    if not isinstance(payload, dict):
        return {}
    try:
        external = copy.deepcopy(payload)
        external.pop('fee_records', None)
        students = external.get('students')
        if isinstance(students, list):
            for student in students:
                if isinstance(student, dict):
                    student.pop('fees', None)
        return external
    except Exception:
        external = dict(payload)
        external.pop('fee_records', None)
        return external
