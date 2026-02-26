# src/infrastructure/course_config_reader.py

import json
from typing import List

from ..scheduling.course import Course


class CourseConfigReader:
    """
    Reads course configuration from a JSON file.
    This allows users to manually define courses with codes, groups, and preferences.
    In the future, this will be replaced by a GUI input.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load_courses(self) -> List[Course]:
        """
        Load courses from JSON configuration file.
        
        Expected JSON structure:
        {
          "courses": [
            {
              "code": "MAT101",
              "name": "Matemáticas I",  // Optional, for documentation
              "number_of_groups": 2,
              "duration": 2,
              "room_type": "REGULAR" or "LAB",  // Optional, auto-detected from code
              "suggested_classroom": "601" or null
            }
          ]
        }
        
        Room type is automatically determined from course code:
        - Ends with 'L' or 'P' → LAB
        - Otherwise → REGULAR
        
        Returns:
            List[Course]: List of configured courses
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        courses = []
        
        for course_data in data.get("courses", []):
            # Validate required fields
            required_fields = ["code", "number_of_groups", "duration"]
            if not all(field in course_data for field in required_fields):
                print(f"Warning: Skipping invalid course entry: {course_data}")
                continue

            code = course_data["code"]
            
            # Auto-detect room type from code if not explicitly provided
            if "room_type" in course_data:
                room_type = course_data["room_type"]
            else:
                room_type = self._infer_room_type(code)

            # Create Course object
            course = Course(
                code=code,
                number_of_groups=course_data["number_of_groups"],
                duration=course_data["duration"],
                required_room_type=room_type,
                suggested_classroom=course_data.get("suggested_classroom")
            )
            
            courses.append(course)

        return courses

    def _infer_room_type(self, course_code: str) -> str:
        """
        Infer room type from course code.
        
        Rules:
        - Code ends with 'L' → LAB (e.g., BIJ400L)
        - Code ends with 'P' → LAB (e.g., BIJ405P)
        - Otherwise → REGULAR (e.g., BIJ400)
        
        Args:
            course_code: Course code string
            
        Returns:
            "LAB" or "REGULAR"
        """
        code_upper = course_code.strip().upper()
        if code_upper.endswith('L') or code_upper.endswith('P'):
            return "LAB"
        return "REGULAR"
