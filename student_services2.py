#!/usr/bin/env python3
"""
Student Information System
==========================
A CLI-based app for managing student records.
Stores data in JSON, supports Add, View, Update, Delete.

Run:
    python student_info_system.py
"""

import os
import json
import uuid
import logging
from datetime import datetime

# ---------------------------
# Utilities and Config Setup
# ---------------------------

DATA_FILE = "data/students.json"
LOG_FILE = "logs/app.log"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def ensure_dirs():
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)


def now():
    return datetime.now().strftime(DATE_FORMAT)


# ---------------------------
# Student Model
# ---------------------------

class Student:
    def __init__(self, name, email, course, year_level, gpa=0.0, student_id=None, created_at=None, updated_at=None):
        self.student_id = student_id or str(uuid.uuid4())[:8]
        self.name = name
        self.email = email
        self.course = course
        self.year_level = year_level
        self.gpa = float(gpa)
        self.created_at = created_at or now()
        self.updated_at = updated_at or now()

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "course": self.course,
            "year_level": self.year_level,
            "gpa": self.gpa,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return Student(
            name=data["name"],
            email=data["email"],
            course=data["course"],
            year_level=data["year_level"],
            gpa=data.get("gpa", 0.0),
            student_id=data.get("student_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


# ---------------------------
# Student Service
# ---------------------------

class StudentService:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        ensure_dirs()
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump([], f)

    def _load_students(self):
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_students(self, students):
        with open(self.data_file, "w") as f:
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
        for s in students:
            if s["student_id"] == student_id:
                return s
        return None

    def update_student(self, student_id, update_data):
        students = self._load_students()
        for s in students:
            if s["student_id"] == student_id:
                s.update(update_data)
                s["updated_at"] = now()
                self._save_students(students)
                return s
        return None

    def delete_student(self, student_id):
        students = self._load_students()
        new_students = [s for s in students if s["student_id"] != student_id]
        if len(new_students) == len(students):
            return False
        self._save_students(new_students)
        return True


# ---------------------------
# Main Application
# ---------------------------

class StudentInformationSystem:
    def __init__(self):
        ensure_dirs()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("SIS")
        self.service = StudentService()

    def display_menu(self):
        print("\n=== Student Information System ===")
        print("1. Add Student")
        print("2. View All Students")
        print("3. View Student by ID")
        print("4. Update Student")
        print("5. Delete Student")
        print("6. Exit")

    def add_student(self):
        print("\n--- Add New Student ---")
        name = input("Name: ")
        email = input("Email: ")
        course = input("Course: ")
        year = input("Year Level: ")
        gpa = input("GPA (optional, press Enter to skip): ")

        try:
            student_data = {
                "name": name,
                "email": email,
                "course": course,
                "year_level": year,
                "gpa": float(gpa) if gpa else 0.0
            }
            student = self.service.add_student(student_data)
            print(f"✅ Student added successfully! ID: {student['student_id']}")
            self.logger.info(f"Added student {student['student_id']}")
        except Exception as e:
            print(f"❌ Error adding student: {e}")
            self.logger.error(f"Error adding student: {e}")

    def view_all_students(self):
        print("\n--- All Students ---")
        students = self.service.get_all_students()
        if not students:
            print("No students found.")
            return
        for s in students:
            print(f"ID: {s['student_id']} | Name: {s['name']} | Email: {s['email']} | Course: {s['course']} | Year: {s['year_level']} | GPA: {s['gpa']}")

    def view_student_by_id(self):
        sid = input("Enter Student ID: ")
        student = self.service.get_student(sid)
        if student:
            print("\n--- Student Details ---")
            for k, v in student.items():
                print(f"{k}: {v}")
        else:
            print("❌ Student not found.")

    def update_student(self):
        sid = input("Enter Student ID to update: ")
        student = self.service.get_student(sid)
        if not student:
            print("❌ Student not found.")
            return
        print("Leave blank to keep current value.")
        name = input(f"Name [{student['name']}]: ") or student['name']
        email = input(f"Email [{student['email']}]: ") or student['email']
        course = input(f"Course [{student['course']}]: ") or student['course']
        year = input(f"Year Level [{student['year_level']}]: ") or student['year_level']
        gpa = input(f"GPA [{student['gpa']}]: ") or student['gpa']

        updated = self.service.update_student(sid, {
            "name": name,
            "email": email,
            "course": course,
            "year_level": year,
            "gpa": float(gpa)
        })
        if updated:
            print("✅ Student updated successfully.")
            self.logger.info(f"Updated student {sid}")
        else:
            print("❌ Update failed.")

    def delete_student(self):
        sid = input("Enter Student ID to delete: ")
        confirm = input("Are you sure? (y/n): ").lower()
        if confirm != "y":
            print("Cancelled.")
            return
        if self.service.delete_student(sid):
            print("✅ Student deleted successfully.")
            self.logger.info(f"Deleted student {sid}")
        else:
            print("❌ Student not found.")

    def run(self):
        while True:
            self.display_menu()
            choice = input("Enter choice (1–6): ").strip()
            if choice == "1":
                self.add_student()
            elif choice == "2":
                self.view_all_students()
            elif choice == "3":
                self.view_student_by_id()
            elif choice == "4":
                self.update_student()
            elif choice == "5":
                self.delete_student()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("Invalid choice, try again.")


# ---------------------------
# Entry Point
# ---------------------------

if __name__ == "__main__":
    app = StudentInformationSystem()
    app.run()
