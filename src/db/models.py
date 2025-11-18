from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(INTEGER, primary_key=True, nullable=False)
    employee_id = Column(TEXT, nullable=False)
    name = Column(TEXT, nullable=False)
    email = Column(TEXT, nullable=False)
    password_hash = Column(TEXT, nullable=False)
    grade = Column(TEXT, nullable=False)
    department = Column(TEXT, nullable=False)
    designation = Column(TEXT, nullable=False)
    role = Column(TEXT, nullable=False)
    manager_id = Column(TEXT, ForeignKey('users.employee_id'))
    is_active = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    city = Column(TEXT)
    gender = Column(VARCHAR(20))

    users = relationship('Users', backref='users_set', cascade='all, delete')


class TravelGrades(Base):
    __tablename__ = 'travel_grades'

    id = Column(INTEGER, primary_key=True, nullable=False)
    grade = Column(TEXT, nullable=False)
    daily_food_allowance = Column(NUMERIC(10, 2), nullable=False)
    daily_travel_allowance = Column(NUMERIC(10, 2), nullable=False)
    daily_lodging_allowance = Column(NUMERIC(10, 2), nullable=False)
    max_flight_budget = Column(NUMERIC(10, 2), nullable=False)
    insurance_coverage = Column(NUMERIC(10, 2), nullable=False)
    created_at = Column(TIMESTAMP)


class TiedUpHotels(Base):
    __tablename__ = 'tied_up_hotels'

    id = Column(INTEGER, primary_key=True, nullable=False)
    hotel_name = Column(TEXT, nullable=False)
    city = Column(TEXT, nullable=False)
    address = Column(TEXT, nullable=False)
    contact_email = Column(TEXT)
    contact_phone = Column(TEXT)
    standard_room_rate = Column(NUMERIC(10, 2), nullable=False)
    corporate_discount = Column(NUMERIC(5, 2))
    final_corporate_rate = Column(NUMERIC(10, 2), nullable=False)
    grade_eligibility = Column(TEXT)
    is_active = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)


class Sessions(Base):
    __tablename__ = 'sessions'

    id = Column(INTEGER, primary_key=True, nullable=False)
    session_id = Column(VARCHAR(255), nullable=False)
    employee_id = Column(VARCHAR(50), nullable=False, ForeignKey('users.employee_id'))
    created_at = Column(TIMESTAMP)
    last_activity_at = Column(TIMESTAMP)

    users = relationship('Users', backref='sessions_set', cascade='all, delete')


class ApprovalWorkflow(Base):
    __tablename__ = 'approval_workflow'

    id = Column(INTEGER, primary_key=True, nullable=False)
    indent_id = Column(TEXT, nullable=False)
    approver_id = Column(TEXT, nullable=False, ForeignKey('users.employee_id'))
    approval_type = Column(TEXT, nullable=False)
    status = Column(TEXT, nullable=False)
    comments = Column(TEXT)
    approved_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    users = relationship('Users', backref='approval_workflow_set', cascade='all, delete')


class Reminders(Base):
    __tablename__ = 'reminders'

    id = Column(INTEGER, primary_key=True, nullable=False)
    indent_id = Column(TEXT, nullable=False)
    reminder_type = Column(TEXT, nullable=False)
    sent_to = Column(TEXT, nullable=False, ForeignKey('users.employee_id'))
    message = Column(TEXT, nullable=False)
    is_sent = Column(BOOLEAN)
    sent_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    users = relationship('Users', backref='reminders_set', cascade='all, delete')


class TravelPolicies(Base):
    __tablename__ = 'travel_policies'

    id = Column(INTEGER, primary_key=True, nullable=False)
    policy_title = Column(TEXT, nullable=False)
    policy_content = Column(TEXT, nullable=False)
    applicable_grades = Column(TEXT)
    effective_date = Column(DATE, nullable=False)
    is_active = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)


class TravelIndents(Base):
    __tablename__ = 'travel_indents'

    id = Column(INTEGER, primary_key=True, nullable=False)
    indent_id = Column(TEXT, nullable=False)
    employee_id = Column(TEXT, nullable=False, ForeignKey('users.employee_id'))
    employee_name = Column(TEXT, nullable=False)
    email = Column(TEXT, nullable=False)
    grade = Column(TEXT, nullable=False)
    department = Column(TEXT, nullable=False)
    designation = Column(TEXT, nullable=False)
    purpose_of_booking = Column(TEXT, nullable=False)
    travel_type = Column(TEXT, nullable=False)
    travel_start_date = Column(DATE, nullable=False)
    travel_end_date = Column(DATE, nullable=False)
    from_city = Column(TEXT, nullable=False)
    from_country = Column(TEXT, nullable=False)
    to_city = Column(TEXT, nullable=False)
    to_country = Column(TEXT, nullable=False)
    total_days = Column(INTEGER)
    created_at = Column(TIMESTAMP)
    is_approved = Column(TEXT)
    updated_at = Column(TIMESTAMP)

    users = relationship('Users', backref='travel_indents_set', cascade='all, delete')


class Notifications(Base):
    __tablename__ = 'notifications'

    id = Column(INTEGER, primary_key=True, nullable=False)
    user_id = Column(TEXT, nullable=False)
    title = Column(TEXT, nullable=False)
    message = Column(TEXT, nullable=False)
    ref_indent_id = Column(TEXT)
    type = Column(TEXT)
    is_read = Column(BOOLEAN)
    created_at = Column(TIMESTAMP)


