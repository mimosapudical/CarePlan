import json
import logging
import os


GEMINI_MODEL = "gemini-2.5-flash"


def _build_prompt(payload: dict) -> str:
    patient_name = f"{payload.get('patient_first_name', '').strip()} {payload.get('patient_last_name', '').strip()}".strip()
    prompt_payload = {
        "patient_name": patient_name or "Not provided",
        "referring_provider": payload.get("referring_provider", ""),
        "patient_primary_diagnosis": payload.get("patient_primary_diagnosis", ""),
        "medication_name": payload.get("medication_name", ""),
        "additional_diagnosis": payload.get("additional_diagnosis", []),
        "medication_history": payload.get("medication_history", []),
        "patient_records": payload.get("patient_records", ""),
    }
    return f"""
You are a clinical care plan drafting assistant for a pharmacist-led care plan workflow.

Draft a concise care plan from the patient information below.

Return ONLY valid JSON with exactly these keys:
- problem_list: array of strings
- goals: array of strings
- pharmacist_interventions: array of strings
- monitoring_plan: array of strings

Do not include markdown, comments, or extra keys.

Patient information:
{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}
""".strip()


def _validate_care_plan(data: dict) -> dict[str, list[str]]:
    required_sections = [
        "problem_list",
        "goals",
        "pharmacist_interventions",
        "monitoring_plan",
    ]

    care_plan = {}
    for section in required_sections:
        items = data.get(section, [])
        if not isinstance(items, list):
            items = [str(items)]
        care_plan[section] = [str(item) for item in items if str(item).strip()]

    return care_plan


def generate_care_plan(payload: dict) -> dict[str, list[str]]:
    logging.info("generate_care_plan: started")

    project = os.environ.get("GCP_PROJECT")
    location = os.environ.get("GCP_LOCATION")
    if not project or not location:
        raise ValueError("GCP_PROJECT and GCP_LOCATION must be set in .env")

    from google import genai
    from google.genai.types import GenerateContentConfig, HttpOptions

    prompt = _build_prompt(payload)
    logging.info(
        "generate_care_plan: calling Gemini model=%s project_present=%s location=%s prompt_length=%s",
        GEMINI_MODEL,
        bool(project),
        location,
        len(prompt),
    )

    client = genai.Client(
        vertexai=True,
        project=project,
        location=location,
        http_options=HttpOptions(api_version="v1"),
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    logging.info("generate_care_plan: Gemini response received")
    care_plan = _validate_care_plan(json.loads(response.text))
    logging.info(
        "generate_care_plan: completed problem_count=%s goal_count=%s intervention_count=%s monitoring_count=%s",
        len(care_plan["problem_list"]),
        len(care_plan["goals"]),
        len(care_plan["pharmacist_interventions"]),
        len(care_plan["monitoring_plan"]),
    )
    return care_plan
