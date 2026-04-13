from core.cv.cv_service import CVService

# Load your test files
with open("test_cv.txt", "r", encoding="utf-8") as f:
    cv_text = f.read()

with open("job.txt", "r", encoding="utf-8") as f:
    job_text = f.read()

service = CVService()

result = service.tailor_cv(cv_text, job_text)

print("\n====================")
print("FIT DECISION")
print("====================")
print(result["fit_decision"])
print(result["fit_summary"])

print("\n====================")
print("RECOMMENDATIONS")
print("====================")
for r in result["recommendations"]:
    print("-", r)

print("\n====================")
print("TAILORED CV (PREVIEW)")
print("====================")
print(result["cv"][:2000])  # preview first part