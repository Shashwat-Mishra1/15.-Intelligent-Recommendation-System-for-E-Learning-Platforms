import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _text(value):
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def recommend_courses(courses, interests="", skills="", quiz_average=None,
                      completed_course_ids=None, enrolled_course_ids=None, limit=4):
    completed_course_ids = set(completed_course_ids or [])
    enrolled_course_ids = set(enrolled_course_ids or [])
    candidates = [
        course for course in courses
        if course.id not in completed_course_ids and course.id not in enrolled_course_ids
    ]
    if not candidates:
        return []
    profile = _text(f"{interests} {skills}")
    documents = [
        _text(f"{course.title} {course.category} {course.level} {course.skills} {course.description}")
        for course in candidates
    ]
    if profile:
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            matrix = vectorizer.fit_transform([profile] + documents)
            similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        except ValueError:
            similarities = [0.0] * len(candidates)
    else:
        similarities = [0.0] * len(candidates)

    results = []
    for course, similarity in zip(candidates, similarities):
        score = float(similarity) * 70
        course_text = _text(f"{course.title} {course.category} {course.skills}")
        matched = [term for term in re.split(r"[,; ]+", profile) if len(term) > 2 and term in course_text]
        if matched:
            score += min(20, len(set(matched)) * 5)
        if quiz_average is not None:
            if quiz_average >= 80 and course.level.lower() == "advanced":
                score += 8
            elif quiz_average < 50 and course.level.lower() == "beginner":
                score += 8
            elif 50 <= quiz_average < 80 and course.level.lower() == "intermediate":
                score += 5
        reason = "Matches your interests and skills" if similarity > 0.05 or matched else "A useful course to broaden your learning"
        if quiz_average is not None:
            reason += "; level adjusted using quiz performance"
        results.append({
            "course_id": course.id, "title": course.title, "category": course.category,
            "level": course.level, "skills": course.skills or "",
            "description": course.description or "", "score": round(min(score, 100), 1),
            "reason": reason
        })
    results.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return results[:limit]
