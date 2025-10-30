#!/usr/bin/env python3
"""
student_info_system.py

Single-file Student Information System with:
- Add / View all / View by ID / Update / Delete students
- JSON or XML storage (configurable)
- Configuration management (creates config if missing)
- Logging to logs/app.log and console
- Simple validation and error handling
- Uses UUIDs for student IDs

To run:
    python student_info_system.py
"""
import os
import json
import uuid
from datetime import datetime
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

# --------------------------
# Configuration / constants
# --------------------------
DEFAULT_CONFIG = {
    "data_file": "data/students.json",
    "storage_format": "json",         # "json" or "xml"
    "log_file": "logs/app.log",
    "date_format": "%Y-%m-%dT%H:%M:%S"
}
CONFIG_PATH = "config/config.json"


# --------------------------
# Utilities
# --------------------------
def ensure_dirs_for_file(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def read_config(path: str = CONFIG_PATH) -> dict:
    ensure_dirs_for_file(path)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, "r") as f:
            cfg = json.load(f)
        # fill missing keys from DEFAULT_CONFIG
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except (json.JSONDecodeError, FileNotFoundError):
        # restore default if corrupted
        with open(path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()


def now_iso(fmt: str = "%Y-%m-%dT%H:%M:%S") -> str:
    return datetime.now().strftime(fmt)


def is_valid_email(email: str) -> bool:
    # simple email validation
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))


# --------------------------
# Student model
# --------------------------
class Student:
    def __init__(
        self,
        name: str,
        email: str,
        course: str,
        year_level: str,
        gpa: float = 0.0,
        student_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.student_id = student_id or str(uuid.uuid4())[:8]
        self.name = name
        self.email = email
        self.course = course
        self.year_level = year_level
        self.gpa = float(gpa)
        self.created_at = created_at or now_iso(DEFAULT_CONFIG["date_format"])
        self.updated_at = updated_at or now_iso(DEFAULT_CONFIG["date_format"])

    def to_dict(self) -> Dict:
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
    def from_dict(d: Dict) -> "Student":
        return Student(
            name=d.get("name", ""),
            email=d.get("email", ""),
            course=d.get("course", ""),
            year_level=d.get("year_level", ""),
            gpa=d.get("gpa", 0.0),
            student_id=d.get("student_id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at")
        )


# --------------------------
# Persistence (JSON / XML)
# --------------------------
class Storage:
    def __init__(self, data_file: str, storage_format: str = "json"):
        self.data_file = data_file
        self.format = storage_format.lower()
        ensure_dirs_for_file(self.data_file)
        # ensure file exists
        if not os.path.exists(self.data_file):
            if self.format == "json":
                with open(self.data_file, "w") as f:
                    json.dump([], f)
            else:
                # create basic XML root
                root = ET.Element("students")
                tree = ET.ElementTree(root)
                tree.write(self.data_file, encoding="utf-8", xml_declaration=True)

    def load(self) -> List[Dict]:
        try:
            if self.format == "json":
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    else:
                        return []
            else:
                tree = ET.parse(self.data_file)
                root = tree.getroot()
                students = []
                for s_elem in root.findall("student"):
                    d = {}
                    for child in s_elem:
                        text = child.text if child.text is not None else ""
                        # try to convert gpa
                        if child.tag == "gpa":
                            try:
                                d["gpa"] = float(text)
                            except ValueError:
                                d["gpa"] = 0.0
                        else:
                            d[child.tag] = text
                    students.append(d)
                return students
        except (FileNotFoundError, json.JSONDecodeError, ET.ParseError):
            return []

    def save(self, students: List[Dict]):
        ensure_dirs_for_file(self.data_file)
        if self.format == "json":
            with open(self.data_file, "w") as f:
                json.dump(students, f, indent=2)
        else:
            root = ET.Element("students")
            for s in students:
                s_elem = ET.SubElement(root, "student")
                for k, v in s.items():
                    child = ET.SubElement(s_elem, k)
                    child.text = str(v)
            tree = ET.ElementTree(root)
            tree.write(self.data_file, encoding="utf-8", xml_declaration=True)


# --------------------------
# Student service (business logic)
# --------------------------
class StudentService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def add_student(self, student_data: dict) -> Dict:
        if not student_data.get("name"):
            raise ValueError("Name is required.")
        if not student_data.get("email") or not is_valid_email(student_data["email"]):
            raise ValueError("A valid email is required.")
        students = self.storage.load()
        student = Student(
            name=student_data["name"],
            email=student_data["email"],
            course=student_data.get("course", ""),
            year_level=student_data.get("year_level", ""),
            gpa=student_data.get("gpa", 0.0)
        )
        students.append(student.to_dict())
        self.storage.save(students)
        return student.to_dict()

    def get_all_students(self) -> List[Dict]:
        return self.storage.load()

    def get_student(self, student_id: str) -> Optional[Dict]:
        students = self.storage.load()
        for s in students:
            if s.get("student_id") == student_id:
                return s
        return None

    def update_student(self, student_id: str, update_data: dict) -> Optional[Dict]:
        students = self.storage.load()
        found = False
        for s in students:
            if s.get("student_id") == student_id:
                found = True
                # only allow certain fields to be updated
                for key in ("name", "email", "course", "year_level", "gpa"):
                    if key in update_data:
                        if key == "email" and not is_valid_email(update_data["email"]):
                            raise ValueError("Invalid email format.")
                        if key == "gpa":
                            try:
                                s[key] = float(update_data[key])
                            except ValueError:
                                s[key] = 0.0
                        else:
                            s[key] = update_data[key]
                s["updated_at"] = now_iso(DEFAULT_CONFIG["date_format"])
                break
        if not found:
            return None
        self.storage.save(students)
        return s

    def delete_student(self, student_id: str) -> bool:
        students = self.storage.load()
        new_students = [s for s in students if s.get("student_id") != student_id]
        if len(new_students) == len(students):
            return False
        self.storage.save(new_students)
        return True


# --------------------------
# CLI Application
# --------------------------
class StudentInformationSystem:
    def __init__(self):
        # load config
        self.config = read_config(CONFIG_PATH)
        # ensure log dir
        ensure_dirs_for_file(self.config.get("log_file", DEFAULT_CONFIG["log_file"]))

        # logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.config.get("log_file", DEFAULT_CONFIG["log_file"])),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("StudentInfoSystem")
        # storage
        storage = Storage(
            data_file=self.config.get("data_file", DEFAULT_CONFIG["data_file"]),
            storage_format=self.config.get("storage_format", DEFAULT_CONFIG["storage_format"])
        )
        self.service = StudentService(storage)

    def display_menu(self):
        print("\n=== Student Information System ===")
        print("1. Add Student")
        print("2. View All Students")
        print("3. View Student by ID")
        print("4. Update Student")
        print("5. Delete Student")
        print("6. Change storage format (json/xml)")
        print("7. Exit")

    def cmd_add_student(self):
        print("\n--- Add New Student ---")
        try:
            name = input("Name: ").strip()
            email = input("Email: ").strip()
            course = input("Course: ").strip()
            year_level = input("Year Level: ").strip()
            gpa_str = input("GPA (optional, default 0.0): ").strip()
            gpa = float(gpa_str) if gpa_str else 0.0

            student_data = {
                "name": name,
                "email": email,
                "course": course,
                "year_level": year_level,
                "gpa": gpa
            }
            student = self.service.add_student(student_data)
            self.logger.info(f"Added student {student['student_id']} - {student['name']}")
            print(f"Student added successfully! ID: {student['student_id']}")
        except Exception as e:
            self.logger.error(f"Error adding student: {e}")
            print(f"Error: {e}")

    def cmd_view_all(self):
        print("\n--- All Students ---")
        students = self.service.get_all_students()
        if not students:
            print("No students found.")
            return
        for s in students:
            print(f"ID: {s.get('student_id')}, Name: {s.get('name')}, Email: {s.get('email')}, "
                  f"Course: {s.get('course')}, Year: {s.get('year_level')}, GPA: {s.get('gpa')}")

    def cmd_view_by_id(self):
        student_id = input("Enter Student ID: ").strip()
        s = self.service.get_student(student_id)
        if not s:
            print("Student not found.")
        else:
            print("\nStudent Details:")
            for k, v in s.items():
                print(f"  {k}: {v}")

    def cmd_update_student(self):
        student_id = input("Enter Student ID to update: ").strip()
        s = self.service.get_student(student_id)
        if not s:
            print("Student not found.")
            return
        print("Leave blank to keep current value.")
        name = input(f"Name [{s.get('name')}]: ").strip()
        email = input(f"Email [{s.get('email')}]: ").strip()
        course = input(f"Course [{s.get('course')}]: ").strip()
        year_level = input(f"Year Level [{s.get('year_level')}]: ").strip()
        gpa_str = input(f"GPA [{s.get('gpa')}]: ").strip()
        update_data = {}
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if course:
            update_data["course"] = course
        if year_level:
            update_data["year_level"] = year_level
        if gpa_str:
            try:
                update_data["gpa"] = float(gpa_str)
            except ValueError:
                print("Invalid GPA entered; skipping GPA update.")
        try:
            updated = self.service.update_student(student_id, update_data)
            if updated:
                self.logger.info(f"Updated student {student_id}")
                print("Student updated successfully.")
            else:
                print("Student not found.")
        except Exception as e:
            self.logger.error(f"Error updating student: {e}")
            print(f"Error: {e}")

    def cmd_delete_student(self):
        student_id = input("Enter Student ID to delete: ").strip()
        confirm = input(f"Are you sure you want to delete student {student_id}? (y/N): ").strip().lower()
        if confirm != "y":
            print("Delete canceled.")
            return
        ok = self.service.delete_student(student_id)
        if ok:
            self.logger.info(f"Deleted student {student_id}")
            print("Student deleted successfully.")
        else:
            print("Student not found.")

    def cmd_change_storage_format(self):
        current = self.config.get("storage_format", "json")
        print(f"Current storage format: {current}")
        new = input("Enter new format (json/xml): ").strip().lower()
        if new not in ("json", "xml"):
            print("Invalid choice.")
            return
        self.config["storage_format"] = new
        # write config
        ensure_dirs_for_file(CONFIG_PATH)
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)
        print(f"Storage format changed to {new}.")
        self.logger.info(f"Storage format changed to {new}. Please restart the app to apply fully.")

    def run(self):
        try:
            while True:
                self.display_menu()
                choice = input("Enter your choice (1-7): ").strip()
                if choice == "1":
                    self.cmd_add_student()
                elif choice == "2":
                    self.cmd_view_all()
                elif choice == "3":
                    self.cmd_view_by_id()
                elif choice == "4":
                    self.cmd_update_student()
                elif choice == "5":
                    self.cmd_delete_student()
                elif choice == "6":
                    self.cmd_change_storage_format()
                elif choice == "7":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Try again.")
        except KeyboardInterrupt:
            print("\nExiting (keyboard interrupt). Goodbye!")
        except Exception as exc:
            self.logger.exception("Unhandled exception in application: %s", exc)
            print(f"An unexpected error occurred: {exc}")


# --------------------------
# Entry point
# --------------------------
if __name__ == "__main__":
    app = StudentInformationSystem()
    app.run()
