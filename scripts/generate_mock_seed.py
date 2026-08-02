from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "mock_data" / "seed_careplan_postgres.sql"


CARE_PLANS = [
    {
        "id": "11111111-1111-4111-8111-111111111111",
        "status": "completed",
        "history": ["pending", "processing", "completed"],
        "payload": {
            "patient_first_name": "Avery",
            "patient_last_name": "Bennett",
            "referring_provider": "Dr. Emily Smith",
            "referring_provider_npi": "1234567890",
            "patient_mrn": "000123",
            "patient_primary_diagnosis": "G70.00",
            "medication_name": "IVIG",
            "additional_diagnosis": ["I10", "K21.9"],
            "medication_history": ["Pyridostigmine 60 mg PO q6h PRN", "Prednisone 10 mg PO daily"],
            "patient_records": "AChR antibody positive MGFA class IIb. Reports fatigable ptosis and dysphagia during flares. Hypertension controlled; GERD managed with PPI.",
        },
        "care_plan": {
            "problem_list": [
                "Generalized myasthenia gravis with intermittent bulbar symptoms.",
                "Chronic corticosteroid exposure requiring safety monitoring.",
            ],
            "goals": [
                "Reduce frequency and severity of myasthenic symptoms.",
                "Maintain safe IVIG administration without infusion reaction.",
            ],
            "pharmacist_interventions": [
                "Verify IVIG dose, weight basis, lot documentation, and infusion schedule before dispense.",
                "Review premedication plan, hydration status, and thrombotic risk factors.",
            ],
            "monitoring_plan": [
                "Track symptom response, strength, swallowing, and respiratory symptoms after each cycle.",
                "Monitor blood pressure, renal function, hydration, and adverse infusion events.",
            ],
        },
        "queued_at": "2026-07-28 09:15:15+00",
        "created_at": "2026-07-28 09:15:00+00",
        "updated_at": "2026-07-28 09:17:00+00",
    },
    {
        "id": "22222222-2222-4222-8222-222222222222",
        "status": "completed",
        "history": ["pending", "processing", "completed"],
        "payload": {
            "patient_first_name": "Jordan",
            "patient_last_name": "Lee",
            "referring_provider": "Dr. Daniel Nguyen",
            "referring_provider_npi": "1987654321",
            "patient_mrn": "000124",
            "patient_primary_diagnosis": "M06.9",
            "medication_name": "Adalimumab",
            "additional_diagnosis": ["E78.5"],
            "medication_history": ["Methotrexate 15 mg weekly", "Folic acid 1 mg daily", "Ibuprofen PRN"],
            "patient_records": "Moderate RA activity despite methotrexate. Baseline TB screening negative. Patient prefers citrate-free autoinjector.",
        },
        "care_plan": {
            "problem_list": [
                "Moderate rheumatoid arthritis with inadequate response to methotrexate alone.",
                "New biologic therapy start requiring infection screening and self-injection education.",
            ],
            "goals": [
                "Improve joint pain, stiffness, and functional activity within expected treatment window.",
                "Prevent avoidable infection and injection technique errors.",
            ],
            "pharmacist_interventions": [
                "Confirm TB and hepatitis screening status before first shipment.",
                "Provide injection training, storage instructions, and missed-dose guidance.",
            ],
            "monitoring_plan": [
                "Assess joint symptoms, morning stiffness, and functional improvement at refill calls.",
                "Screen for fever, persistent cough, injection site reaction, or new neurologic symptoms.",
            ],
        },
        "queued_at": "2026-07-29 14:05:20+00",
        "created_at": "2026-07-29 14:05:00+00",
        "updated_at": "2026-07-29 14:07:00+00",
    },
    {
        "id": "33333333-3333-4333-8333-333333333333",
        "status": "completed",
        "history": ["pending", "processing", "completed"],
        "payload": {
            "patient_first_name": "Maya",
            "patient_last_name": "Rodriguez",
            "referring_provider": "Dr. Michael Carter",
            "referring_provider_npi": "1122334455",
            "patient_mrn": "000125",
            "patient_primary_diagnosis": "K50.90",
            "medication_name": "Ustekinumab",
            "additional_diagnosis": ["D50.9", "K21.9"],
            "medication_history": ["Budesonide taper", "Ferrous sulfate 325 mg daily", "Omeprazole 20 mg daily"],
            "patient_records": "Crohn's disease with recurrent abdominal pain and elevated fecal calprotectin. Iron deficiency anemia under treatment.",
        },
        "care_plan": {
            "problem_list": [
                "Active Crohn's disease requiring specialty biologic therapy.",
                "Iron deficiency anemia may reflect disease activity or nutritional deficiency.",
            ],
            "goals": [
                "Reduce GI symptoms and inflammatory markers.",
                "Maintain adherence to induction and maintenance schedule.",
            ],
            "pharmacist_interventions": [
                "Confirm induction dose completion and maintenance injection timing.",
                "Educate on infection precautions, storage, and sharps disposal.",
            ],
            "monitoring_plan": [
                "Monitor abdominal pain, stool frequency, bleeding, weight, and fatigue.",
                "Assess infection symptoms and injection tolerability at each contact.",
            ],
        },
        "queued_at": "2026-07-30 10:30:10+00",
        "created_at": "2026-07-30 10:30:00+00",
        "updated_at": "2026-07-30 10:32:00+00",
    },
    {
        "id": "44444444-4444-4444-8444-444444444444",
        "status": "processing",
        "history": ["pending", "processing"],
        "payload": {
            "patient_first_name": "Noah",
            "patient_last_name": "Kim",
            "referring_provider": "Dr. Priya Patel",
            "referring_provider_npi": "1098765432",
            "patient_mrn": "000126",
            "patient_primary_diagnosis": "L20.9",
            "medication_name": "Dupilumab",
            "additional_diagnosis": ["J45.909"],
            "medication_history": ["Triamcinolone 0.1% ointment", "Cetirizine 10 mg daily"],
            "patient_records": "Severe atopic dermatitis with sleep disruption and inadequate response to topical therapy. Mild intermittent asthma history.",
        },
        "care_plan": None,
        "queued_at": "2026-07-31 16:40:15+00",
        "created_at": "2026-07-31 16:40:00+00",
        "updated_at": "2026-07-31 16:40:15+00",
    },
    {
        "id": "55555555-5555-4555-8555-555555555555",
        "status": "failed",
        "history": ["pending", "failed"],
        "payload": {
            "patient_first_name": "Sophia",
            "patient_last_name": "Chen",
            "referring_provider": "Dr. Daniel Nguyen",
            "referring_provider_npi": "1987654321",
            "patient_mrn": "000127",
            "patient_primary_diagnosis": "M31.6",
            "medication_name": "Tocilizumab",
            "additional_diagnosis": ["M81.0", "I10"],
            "medication_history": ["Prednisone 40 mg daily", "Alendronate 70 mg weekly", "Amlodipine 5 mg daily"],
            "patient_records": "Giant cell arteritis with steroid-sparing biologic plan. Osteoporosis risk due to prolonged high-dose steroid exposure.",
        },
        "care_plan": None,
        "error": "Mock failure: queue worker unavailable during generation.",
        "queued_at": None,
        "created_at": "2026-08-01 08:55:00+00",
        "updated_at": "2026-08-01 08:55:30+00",
    },
]


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    return "'" + str(value).replace("'", "''") + "'"


def build_sql() -> str:
    rows = []
    for plan in CARE_PLANS:
        rows.append(
            "  ("
            + ", ".join(
                [
                    sql_literal(plan["id"]),
                    sql_literal(plan["status"]),
                    f"{sql_literal(plan['history'])}::jsonb",
                    f"{sql_literal(plan['payload'])}::jsonb",
                    f"{sql_literal(plan.get('care_plan'))}::jsonb" if plan.get("care_plan") is not None else "NULL",
                    sql_literal(plan.get("error")),
                    sql_literal(plan.get("queued_at")),
                    sql_literal(plan["created_at"]),
                    sql_literal(plan["updated_at"]),
                ]
            )
            + ")"
        )

    return "\n".join(
        [
            "-- PostgreSQL mock data for the current Django CarePlan model.",
            "-- Run `python manage.py migrate` first, then run this whole file in TablePlus.",
            "",
            "BEGIN;",
            "",
            "CREATE TABLE IF NOT EXISTS careplans_careplan (",
            "  id UUID PRIMARY KEY,",
            "  status VARCHAR(20) NOT NULL,",
            "  history JSONB NOT NULL,",
            "  payload JSONB NOT NULL,",
            "  care_plan JSONB NULL,",
            "  error TEXT NULL,",
            "  queued_at TIMESTAMPTZ NULL,",
            "  created_at TIMESTAMPTZ NOT NULL,",
            "  updated_at TIMESTAMPTZ NOT NULL",
            ");",
            "",
            "TRUNCATE careplans_careplan;",
            "",
            "INSERT INTO careplans_careplan (",
            "  id, status, history, payload, care_plan, error, queued_at, created_at, updated_at",
            ") VALUES",
            ",\n".join(rows) + ";",
            "",
            "COMMIT;",
            "",
        ]
    )


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_sql(), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
