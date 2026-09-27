import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, ValidationError

app = FastAPI(
    title="Student Service",
    description="A simple FastAPI application for managing students.",
    version="1.0.0",
)


def calculate_final_score(
    assignment_score: float, midterm_score: float, final_score: float
) -> float:
    return 0.2 * assignment_score + 0.3 * midterm_score + 0.5 * final_score


def get_result(score: float) -> str:
    return "Pass" if score >= 5.0 else "Fail"


class Student(BaseModel):
    student_id: str = Field(min_length=1)
    name: str = Field(min_length=2)
    age: int = Field(ge=18, le=60)
    email: EmailStr
    gpa: float = Field(ge=0.0, le=4.0)


def generate_random_students(count: int = 10, invalid_probability: float = 0.3):
    first_names = ["An", "Binh", "Chi", "Duy", "Hoa", "Linh", "Minh", "Nam"]
    last_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vu", "Do"]

    students_data = []

    for i in range(1, count + 1):
        # Generate valid base values
        s_id = f"S{i:03d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(18, 25)
        email = f"{name.lower().replace(' ', '.')}@example.com"
        gpa = round(random.uniform(2.0, 4.0), 2)

        # Randomly introduce invalid data
        if random.random() < invalid_probability:
            error_type = random.choice(
                ["bad_id", "bad_name", "bad_age", "bad_email", "bad_gpa"]
            )

            if error_type == "bad_id":
                s_id = ""  # Violates min_length=1
            elif error_type == "bad_name":
                name = "A"  # Violates min_length=2
            elif error_type == "bad_age":
                age = random.choice([16, 17, 61, 70])  # Violates ge=18, le=60
            elif error_type == "bad_email":
                email = "invalid_email_format"  # Violates EmailStr
            elif error_type == "bad_gpa":
                gpa = round(
                    random.choice([-1.0, 4.5, 5.0]), 2
                )  # Violates ge=0.0, le=4.0

        students_data.append(
            {
                "student_id": s_id,
                "name": name,
                "age": age,
                "email": email,
                "gpa": gpa,
            }
        )

    return students_data


students = generate_random_students()

if __name__ == "__main__":
    valid_students = []
    invalid_students = []

    for data in students:
        try:
            student = Student(**data)
            valid_students.append(student)
        except ValidationError as error:
            invalid_students.append({"data": data, "errors": error.errors()})

    num_valid_students, num_invalid_students = len(valid_students), len(
        invalid_students
    )

    print(
        (
            f"There are {num_valid_students} valid students"
            if num_valid_students > 1
            else (
                "There is a valid student"
                if num_valid_students == 1
                else "There is no valid student"
            )
        ),
        "and",
        (
            f"there are {num_invalid_students} invalid students"
            if num_invalid_students > 1
            else (
                "there is an invalid student"
                if num_invalid_students == 1
                else "there is no invalid student"
            )
        ),
    )

    print("\nValid Students:")
    for student in valid_students:
        print(student)

    print("\nInvalid Students:")
    for student in invalid_students:
        print(f"Data: {student['data']}")

        for error in student["errors"]:
            field = error["loc"][0]
            message = error["msg"]
            print(f"- {field}: {message}")


@app.get("/")
def root():
    return {"service": "Student Service", "course": "504070"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/students")
def get_students():
    return students


@app.get("/students/{student_id}")
def get_student(student_id: str):
    for s in students:
        if s["student_id"] == student_id:
            return s
    raise HTTPException(status_code=404, detail="Student not found")
