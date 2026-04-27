import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Step 1: Preprocessing
def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

# Step 2: TF-IDF + Cosine Similarity
def calculate_similarity(student, model):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([student, model])
    similarity = cosine_similarity(vectors[0], vectors[1])
    return similarity[0][0]

# Step 3: Keyword Matching
def keyword_match(student, keywords):
    student_words = set(student.split())
    matched = [k for k in keywords if k in student_words]
    return matched, len(matched) / len(keywords)

# Step 4: Score + Feedback
def generate_result(similarity, keyword_score):
    final_score = (similarity * 0.7 + keyword_score * 0.3) * 10

    if final_score > 8:
        feedback = "Excellent answer"
    elif final_score > 5:
        feedback = "Good but missing some points"
    else:
        feedback = "Needs improvement"

    return round(final_score, 2), feedback