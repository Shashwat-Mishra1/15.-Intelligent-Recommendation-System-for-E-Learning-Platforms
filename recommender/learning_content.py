"""Starter learning content.

Content is assigned by exact normalized course title for this first version.
No database columns are changed.
"""


PYTHON_LESSONS = [
    {
        "title": "Variables, values, and comments",
        "notes": [
            "A variable name refers to a value. Use = to assign a value.",
            "Strings represent text, integers represent whole numbers, "
            "and floats represent numbers with a fractional part.",
            "A comment starts with # outside a string and continues "
            "to the end of the line.",
            "Use print() to display a value.",
        ],
        "code": (
            '# Store a learner profile\n'
            'name = "Asha"\n'
            'age = 20\n'
            'average_score = 82.5\n'
            '\n'
            'print(name)\n'
            'print(age)\n'
            'print(average_score)\n'
        ),
        "practice": (
            "Create variables for your name, a course title, and a score. "
            "Print all three. Add a comment explaining your code."
        ),
        "resource_title": "Python introduction",
        "resource_url": (
            "https://docs.python.org/3/tutorial/introduction.html"
        ),
    },
    {
        "title": "Lists, dictionaries, and len()",
        "notes": [
            "A list stores an ordered sequence of items.",
            "List indexes start at zero.",
            "A dictionary stores key-value pairs.",
            "len() returns the number of items in a collection.",
        ],
        "code": (
            'topics = ["Variables", "Loops", "Functions"]\n'
            'print(topics[0])\n'
            'print(len(topics))\n'
            '\n'
            'learner = {"name": "Asha", "score": 80}\n'
            'print(learner["name"])\n'
            'print(learner["score"])\n'
        ),
        "practice": (
            "Create a list containing three courses and print its length. "
            "Create a dictionary with a course title and its level."
        ),
        "resource_title": "Python data structures",
        "resource_url": (
            "https://docs.python.org/3/tutorial/datastructures.html"
        ),
    },
    {
        "title": "Conditions and decisions",
        "notes": [
            "Use if to run a block only when a condition is true.",
            "Use elif to check another condition and else for the "
            "remaining case.",
            "Indent the statements belonging to each block.",
            "Comparison operators include ==, !=, <, >, <=, and >=.",
        ],
        "code": (
            'score = 65\n'
            '\n'
            'if score >= 80:\n'
            '    print("Strong result")\n'
            'elif score >= 50:\n'
            '    print("Passing result")\n'
            'else:\n'
            '    print("More practice needed")\n'
        ),
        "practice": (
            "Change score to 35, 50, and 90. Predict the message before "
            "running the program each time."
        ),
        "resource_title": "Python if statements",
        "resource_url": (
            "https://docs.python.org/3/tutorial/controlflow.html"
            "#if-statements"
        ),
    },
    {
        "title": "Repeating work with loops",
        "notes": [
            "A for loop visits the items of an iterable such as a list.",
            "A while loop repeats while its condition is true.",
            "When using while, make sure the program can eventually "
            "make the condition false.",
        ],
        "code": (
            'topics = ["Variables", "Lists", "Functions"]\n'
            '\n'
            'for topic in topics:\n'
            '    print(topic)\n'
            '\n'
            'attempt = 1\n'
            'while attempt <= 3:\n'
            '    print("Practice attempt", attempt)\n'
            '    attempt += 1\n'
        ),
        "practice": (
            "Write a while loop that prints the numbers 1 through 5. "
            "Then use a for loop to print each course in a list."
        ),
        "resource_title": "Python control flow",
        "resource_url": (
            "https://docs.python.org/3/tutorial/controlflow.html"
        ),
    },
    {
        "title": "Reusable code with functions",
        "notes": [
            "Use def to define a function.",
            "Parameters let a function receive input values.",
            "Use return to send a result back to the caller.",
            "A function definition does not execute its body immediately. "
            "Call the function to run it.",
        ],
        "code": (
            'def quiz_percentage(correct, total):\n'
            '    if total <= 0:\n'
            '        return 0.0\n'
            '    return round((correct / total) * 100, 1)\n'
            '\n'
            'result = quiz_percentage(4, 5)\n'
            'print(result)\n'
        ),
        "practice": (
            "Write a function named has_passed(score). Return True "
            "when score is at least 50 and False otherwise. "
            "Try calling it with 40, 50, and 85."
        ),
        "resource_title": "Defining Python functions",
        "resource_url": (
            "https://docs.python.org/3/tutorial/controlflow.html"
            "#defining-functions"
        ),
    },
]


COURSE_CONTENT = {
    "python programming fundamentals": {
        "overview": (
            "A short introduction to Python using notes, worked examples, "
            "and practice exercises. Run the examples in your own "
            "Python environment."
        ),
        "lessons": PYTHON_LESSONS,
    },
}


def get_learning_content(course_title):
    """Return content only for an explicitly assigned course."""
    normalized_title = " ".join(
        (course_title or "").casefold().split()
    )

    return COURSE_CONTENT.get(normalized_title)