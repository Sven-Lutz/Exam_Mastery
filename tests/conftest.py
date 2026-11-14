import os

# The offline suite must never read the user's real provider config (it could start paid runs).
os.environ.setdefault('EXAM_MASTERY_CONFIG', '/nonexistent/exam-mastery-test-isolation/config.json')
