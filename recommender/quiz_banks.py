"""Course-specific quiz banks.

Each question includes:
- question text
- four options
- zero-based correct answer index
- topic label for future topic-level analytics
"""
from recommender.quiz_data import QUIZ_BANK
import random
from flask import session


PYTHON_QUESTION_BANK = [
    {
        "id": "py-001",
        "topic": "Variables",
        "question": "Which keyword creates a variable assignment in Python?",
        "options": ["let", "var", "=", "define"],
        "answer": 2,
    },
    {
        "id": "py-002",
        "topic": "Variables",
        "question": "What is the data type of 3.14?",
        "options": ["int", "float", "str", "bool"],
        "answer": 1,
    },
    {
        "id": "py-003",
        "topic": "Variables",
        "question": "Which value represents True in Python?",
        "options": ["true", "TRUE", "True", "yes"],
        "answer": 2,
    },
    {
        "id": "py-004",
        "topic": "Variables",
        "question": "Which line prints the value stored in name?",
        "options": [
            "print(name)",
            "print 'name'",
            "echo name",
            "display(name)",
        ],
        "answer": 0,
    },
    {
        "id": "py-005",
        "topic": "Variables",
        "question": "Which is a valid Python variable name?",
        "options": ["2score", "student score", "student_score", "class"],
        "answer": 2,
    },
    {
        "id": "py-006",
        "topic": "Lists and dictionaries",
        "question": "How do you access the first item in a list named courses?",
        "options": [
            "courses[1]",
            "courses[0]",
            "courses.first()",
            "courses(0)",
        ],
        "answer": 1,
    },
    {
        "id": "py-007",
        "topic": "Lists and dictionaries",
        "question": "What does len([10, 20, 30]) return?",
        "options": ["2", "3", "30", "60"],
        "answer": 1,
    },
    {
        "id": "py-008",
        "topic": "Lists and dictionaries",
        "question": "Which data structure stores key-value pairs?",
        "options": ["list", "tuple", "dictionary", "integer"],
        "answer": 2,
    },
    {
        "id": "py-009",
        "topic": "Lists and dictionaries",
        "question": "How do you get the value linked to the key \"score\"?",
        "options": [
            "student.score",
            "student[\"score\"]",
            "student->score",
            "student::score",
        ],
        "answer": 1,
    },
    {
        "id": "py-010",
        "topic": "Lists and dictionaries",
        "question": "Which method adds an item to the end of a list?",
        "options": ["add()", "insert()", "append()", "push()"],
        "answer": 2,
    },
    {
        "id": "py-011",
        "topic": "Conditions",
        "question": "Which keyword starts a conditional statement?",
        "options": ["when", "if", "check", "switch"],
        "answer": 1,
    },
    {
        "id": "py-012",
        "topic": "Conditions",
        "question": "Which operator checks whether two values are equal?",
        "options": ["=", "==", "===", "!="],
        "answer": 1,
    },
    {
        "id": "py-013",
        "topic": "Conditions",
        "question": "Which keyword provides an alternative condition?",
        "options": ["otherwise", "elif", "elseif", "case"],
        "answer": 1,
    },
    {
        "id": "py-014",
        "topic": "Conditions",
        "question": "What does this print?\n\nscore = 45\nif score >= 50:\n    print(\"Pass\")\nelse:\n    print(\"Retry\")",
        "options": ["Pass", "Retry", "Nothing", "Error"],
        "answer": 1,
    },
    {
        "id": "py-015",
        "topic": "Conditions",
        "question": "Which comparison means “not equal to”?",
        "options": ["==", "!=", ">=", "<="],
        "answer": 1,
    },
    {
        "id": "py-016",
        "topic": "Loops",
        "question": "Which loop is best for visiting every item in a list?",
        "options": ["for loop", "if statement", "function", "variable"],
        "answer": 0,
    },
    {
        "id": "py-017",
        "topic": "Loops",
        "question": "How many times does this loop run?\n\nfor number in range(3):\n    print(number)",
        "options": ["2", "3", "4", "Infinite"],
        "answer": 1,
    },
    {
        "id": "py-018",
        "topic": "Loops",
        "question": "Which loop repeats while its condition remains true?",
        "options": ["for", "while", "if", "def"],
        "answer": 1,
    },
    {
        "id": "py-019",
        "topic": "Loops",
        "question": "What does range(1, 4) produce?",
        "options": ["1, 2, 3", "1, 2, 3, 4", "0, 1, 2, 3", "4"],
        "answer": 0,
    },
    {
        "id": "py-020",
        "topic": "Loops",
        "question": "Which statement immediately ends the current loop?",
        "options": ["stop", "exit", "break", "return"],
        "answer": 2,
    },
    {
        "id": "py-021",
        "topic": "Functions",
        "question": "Which keyword defines a function?",
        "options": ["function", "def", "define", "func"],
        "answer": 1,
    },
    {
        "id": "py-022",
        "topic": "Functions",
        "question": "What does return do?",
        "options": [
            "Prints a value",
            "Sends a value back to the caller",
            "Creates a variable",
            "Ends Python",
        ],
        "answer": 1,
    },
    {
        "id": "py-023",
        "topic": "Functions",
        "question": "What is the output?\n\ndef add(a, b):\n    return a + b\n\nprint(add(2, 3))",
        "options": ["23", "5", "2 + 3", "Error"],
        "answer": 1,
    },
    {
        "id": "py-024",
        "topic": "Functions",
        "question": "What is the name of the value passed into a function?",
        "options": ["Argument", "Comment", "Loop", "Index"],
        "answer": 0,
    },
    {
        "id": "py-025",
        "topic": "Functions",
        "question": "Which function call is correct for a function defined as def greet(name):?",
        "options": [
            "greet[Asha]",
            "greet(Asha)",
            "greet(\"Asha\")",
            "call greet(Asha)",
        ],
        "answer": 2,
    },
    {
        "id": "py-026",
        "topic": "Variables",
        "question": "Which line creates a string variable?",
        "options": [
            "course = Python",
            "course = \"Python\"",
            "course = 10",
            "course = True",
        ],
        "answer": 1,
    },
    {
        "id": "py-027",
        "topic": "Lists and dictionaries",
        "question": "What is the index of the last item in a four-item list?",
        "options": ["3", "4", "-1", "0"],
        "answer": 0,
    },
    {
        "id": "py-028",
        "topic": "Conditions",
        "question": "Which value makes this condition true?\n\nif score >= 80:",
        "options": ["70", "80", "50", "40"],
        "answer": 1,
    },
    {
        "id": "py-029",
        "topic": "Loops",
        "question": "What does continue do inside a loop?",
        "options": [
            "Ends the program",
            "Skips to the next loop iteration",
            "Repeats the same item forever",
            "Defines a function",
        ],
        "answer": 1,
    },
    {
        "id": "py-030",
        "topic": "Functions",
        "question": "How many required arguments does this function need?\n\ndef calculate(total, discount):",
        "options": ["0", "1", "2", "3"],
        "answer": 2,
    },
]


QUIZ_LENGTH = 15
SESSION_KEY = "last_python_quiz_question_ids"


def _select_questions(available_questions):
    """Select 15 questions, preferring questions not used immediately before."""
    previous_ids = set(session.get(SESSION_KEY, []))

    unused = [
        question for question in available_questions
        if question["id"] not in previous_ids
    ]
    used = [
        question for question in available_questions
        if question["id"] in previous_ids
    ]

    random.shuffle(unused)
    random.shuffle(used)

    selected = unused[:QUIZ_LENGTH]

    if len(selected) < QUIZ_LENGTH:
        remaining = QUIZ_LENGTH - len(selected)
        selected.extend(used[:remaining])

    random.shuffle(selected)

    session[SESSION_KEY] = [
        question["id"] for question in selected
    ]

    return selected


def select_quiz_questions(course):
    """Return course-specific randomized questions when available.

    Courses without a dedicated randomized bank fall back to the
    original quiz bank so existing enrollments remain usable.
    """
    normalized_title = " ".join(
        (course.title or "").casefold().split()
    )

    if normalized_title == "python programming fundamentals":
        return _select_questions(PYTHON_QUESTION_BANK)

    course_text = (
        f"{course.title} {course.skills or ''}"
    ).lower()

    if "python" in course_text:
        bank_key = "python"
    elif any(
        word in course_text
        for word in ("web", "html", "css", "flask", "javascript")
    ):
        bank_key = "web development"
    else:
        bank_key = "general"

    return QUIZ_BANK[bank_key]