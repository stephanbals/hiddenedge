@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        job_text = request.form.get("job_text", "")
        file = request.files.get("file")

        cv_text = extract_cv(file)

        prompt = f"""
You are Nestor, a strict hiring evaluator.

Return ONLY valid JSON. No explanation.

{{
  "fit_score": number,
  "recruiter_view": "...",
  "hiring_manager_view": "...",
  "gaps": ["...", "...", "..."],
  "actions": ["...", "...", "..."],
  "alternative_roles": ["...", "...", "..."]
}}

CV:
{cv_text[:3000]}

JOB:
{job_text[:2000]}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw = response.choices[0].message.content.strip()

        print("=== RAW GPT OUTPUT ===")
        print(raw)

        # SAFE JSON PARSE
        try:
            data = json.loads(raw)
        except:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise Exception("No valid JSON returned")

        # ENSURE DICT
        if not isinstance(data, dict):
            raise Exception("Parsed JSON is not a dict")

        score = int(data.get("fit_score", 0))
        decision = map_decision(score)

        return jsonify({
            "nestor": {
                "decision": decision,
                "fit_score": score,
                "recruiter_view": data.get("recruiter_view", ""),
                "hiring_manager_view": data.get("hiring_manager_view", "")
            }
        })

    except Exception as e:
        print("=== ERROR ===", str(e))

        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error",
                "hiring_manager_view": str(e)
            }
        }), 200