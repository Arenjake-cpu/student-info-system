import json
import os
from ..models.student import Student

class StudentService:
    def __init__(self, data_file='data/students.json'):
        self.data_file = data_file
        self._ensure_data_file()

    def _ensure_data_file(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)

    def _load_students(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_students(self, students):
        with open(self.data_file, 'w') as f:
            json.dump(students, f, indent=2)

    def add_student(self, student_data):
        students = self._load_students()
        student = Student(**student_data)
        students.append(student.to_dict())
        self._save_students(students)
        return student.to_dict()

    def get_all_students(self):
        return self._load_students()

    def get_student(self, student_id):
        students = self._load_students()
        for student in students:
            if student['student_id'] == student_id:
                return student
        return None

    def update_student(self, student_id, update_data):
        students = self._load_students()
        for student in students:
            if student['student_id'] == student_id:
                student.update(update_data)
                student['updated_at'] = datetime.now().isoformat()
                self._save_students(students)
                return student
        return None

    def delete_student(self, student_id):
        students = self._load_students()
        new_students = [s for s in students if s['student_id'] != student_id]
        self._save_students(new_students)
        return len(students) != len(self._load_students())
