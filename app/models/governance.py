from datetime import datetime, date

from app import db


class UserAccessWindow(db.Model):
    __tablename__ = 'user_access_windows'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    month_from = db.Column(db.String(7), nullable=False)  # YYYY-MM
    month_to = db.Column(db.String(7), nullable=False)    # YYYY-MM
    set_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DeviceSession(db.Model):
    __tablename__ = 'device_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    login_id = db.Column(db.String(50), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='student')
    device_id = db.Column(db.String(128), nullable=True, index=True)
    device_name = db.Column(db.String(120), nullable=True)
    os = db.Column(db.String(80), nullable=True)
    browser = db.Column(db.String(80), nullable=True)
    ip = db.Column(db.String(64), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='online')  # online/offline


class AccountAction(db.Model):
    __tablename__ = 'account_actions'

    id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False)  # hold/resume/delete
    reason = db.Column(db.Text, nullable=True)
    by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class JoinCode(db.Model):
    __tablename__ = 'join_codes'

    id = db.Column(db.Integer, primary_key=True)
    code_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class StudentTransfer(db.Model):
    __tablename__ = 'student_transfers'

    id = db.Column(db.Integer, primary_key=True)
    from_student_id = db.Column(db.Integer, nullable=False, index=True)
    to_student_id = db.Column(db.Integer, nullable=False, index=True)
    transfer_type = db.Column(db.String(16), nullable=False)  # points|stars
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    lock_until = db.Column(db.DateTime, nullable=False, index=True)


class Proposal(db.Model):
    __tablename__ = 'proposals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    scope = db.Column(db.String(24), nullable=False, default='student_council')  # student_council|all_students
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    open_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    close_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='open')  # open|closed|archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProposalVote(db.Model):
    __tablename__ = 'proposal_votes'

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False, index=True)
    voter_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    choice = db.Column(db.String(16), nullable=False)  # support|oppose|abstain
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint('proposal_id', 'voter_user_id', name='uq_proposal_vote_once'),
    )


class ProposalMessage(db.Model):
    __tablename__ = 'proposal_messages'

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    login_id = db.Column(db.String(50), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default='student')
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class ScoreAdjustmentAction(db.Model):
    __tablename__ = 'score_adjustment_actions'

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    actor_login_id = db.Column(db.String(50), nullable=False, index=True)
    actor_role = db.Column(db.String(20), nullable=False)  # leader|co_leader
    target_student_id = db.Column(db.Integer, nullable=False, index=True)
    target_date = db.Column(db.Date, nullable=False, index=True)
    delta_points = db.Column(db.Integer, nullable=False)
    mode = db.Column(db.String(24), nullable=False)  # leader_zero|co_leader_reduce
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        db.Index('ix_score_adj_actor_day', 'actor_login_id', 'target_date'),
    )
