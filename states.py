from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_profile_name = State()
    waiting_for_profile_username = State()
    waiting_for_profile_subjects = State()
    waiting_for_profile_cost = State()
    waiting_for_profile_link = State()
    waiting_for_profile_timezone = State()
    waiting_for_new_lesson_date = State()
    waiting_for_new_lesson_time = State()
    waiting_for_vacation_start_date = State()
    waiting_for_vacation_end_date = State()
    waiting_for_vacation_reason = State()
    waiting_for_free_slot = State()
    waiting_for_free_slot_date = State()
    waiting_for_free_slot_time = State()
    waiting_for_notification_settings = State()
    waiting_for_group_lesson_name = State()
    waiting_for_group_lesson_time = State()

class MessageStates(StatesGroup):
    selecting_student = State()
    waiting_for_message_type = State()
    waiting_for_message_content = State()

class HomeworkStates(StatesGroup):
    waiting_for_content = State()
    waiting_for_homework_content = State()
    waiting_for_reminder_date = State()

class GroupLessonStates(StatesGroup):
    waiting_for_group_name = State()
    waiting_for_group_description = State()
    waiting_for_group_members = State()

class ScheduleStates(StatesGroup):
    waiting_for_lesson_datetime = State()
    waiting_for_slot_datetime = State()
    waiting_for_day = State()
    waiting_for_time = State()

class RescheduleStates(StatesGroup):
    waiting_for_new_slot = State()
    waiting_for_new_datetime = State()

class CancelLessonStates(StatesGroup):
    selecting_lesson = State()
    confirming_cancellation = State()

class StudentStates(StatesGroup):
    viewing_schedule = State()
    selecting_lesson = State()
    waiting_for_question = State()
    waiting_for_homework_submission = State()

class StudentHomeworkStates(StatesGroup):
    viewing_homework = State()
    submitting_homework = State()
    waiting_for_submission_type = State()
    waiting_for_submission_content = State()
    waiting_for_file = State()
    waiting_for_text = State()

class StudentQuestionStates(StatesGroup):
    waiting_for_question_text = State()
    waiting_for_question_subject = State()
    confirming_question = State()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_subjects = State()
    waiting_for_timezone = State()
    waiting_for_age = State()
    waiting_for_subject = State()
    confirming_registration = State()
    waiting_for_tutor_choice = State()

class SuperadminStates(StatesGroup):
    waiting_for_role_user_id = State()
    waiting_for_new_role = State()
    waiting_for_tutor_id = State()
    waiting_for_tutor_name = State()
    waiting_for_tutor_username = State()
    waiting_for_tutor_subjects = State()
    waiting_for_tutor_cost = State()
    waiting_for_tutor_link = State()

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_subjects = State()
    waiting_for_cost = State()
    waiting_for_timezone = State()
    waiting_for_link = State()

class MessagingStates(StatesGroup):
    waiting_for_message = State()
    selecting_recipient = State()
