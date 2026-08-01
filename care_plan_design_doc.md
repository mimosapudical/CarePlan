# Care Plan Auto-Generation Tool - Design Document

## 1. Background
Customer: Specialty Pharmacy

Need: Automatically generate a care plan from patient clinical records, replacing manual pharmacist preparation that currently takes 20-40 minutes per patient.

Urgency: Compliance requirements, Medicare/pharma reimbursement requirements, staff shortage, and task backlog.

## 2. Users
- CVS healthcare workers use this system. Patients do not directly access it.
- When prescribing medication, healthcare workers need a care plan. CVS healthcare workers create it, then print it after generation and provide it with the patient materials.

## 3. Care Plan Definition
- One care plan corresponds to one order for one medication.
- Output must include: Problem list, Goals, Pharmacist interventions, Monitoring plan.

## 4. Input Fields
| Field | Type |
|---|---|
| Patient First Name | string |
| Patient Last Name | string |
| Referring Provider | string |
| Referring Provider NPI | 10-digit number |
| Patient MRN (unique ID) | unique 6-digit number |
| Patient Primary Diagnosis | ICD-10 code |
| Medication Name | string |
| Additional Diagnosis | list of ICD-10 codes |
| Medication history | list of strings |
| Patient Records | string or PDF document |

## 5. Functional Requirements
- A medical assistant enters the information above through a web form.
- The web form validates all data.
- Warn when an order appears to be a duplicate.
- Warn when a patient appears to be a duplicate.
- A provider can only be entered once in the system.
- Call an LLM to generate a care plan and output it as a downloadable text file.
- Provide a quick way to export data for pharma reporting.

## 6. Duplicate Detection Rules
| Scenario | Handling | Reason |
|---|---|---|
| Same patient + same medication + same day | ERROR, must block | Risk of duplicate submission |
| Same patient + same medication + different day | WARNING, user can confirm and continue | Could be a refill or renewal |
| Same MRN, different name or DOB | WARNING, user can confirm and continue | Could be a data entry issue |
| Same name + same DOB, different MRN | WARNING, user can confirm and continue | Could be the same person |
| Same NPI, different provider name | ERROR, must fix | NPI is the unique identifier |

## 7. Feature Priority
| Feature | Required | Notes |
|---|---|---|
| Patient/order duplicate detection | Required | Without it, there is no reliable workflow |
| Care plan generation | Required | Core value |
| Provider duplicate detection | Required | Affects pharma reporting |
| Report export | Required | Needed for pharma reporting |
| Care plan download | Required | Users need to upload or provide it to patients |

## 8. Production Readiness Requirements
- Validate all inputs.
- Always enforce consistency rules.
- Errors must be safe, clear, and controllable.
- Code should be modular and easy to navigate.
- Key logic should have automated test coverage.
- The project should run end to end out of the box.

## 9. Example Data (Patient Record Sample)
```text
Name: A.B. (Fictional)
MRN: 00012345 (fictional)
DOB: 1979-06-08 (Age 46)
Sex: Female
Weight: 72 kg
Allergies: None known to medications (no IgA deficiency)
Medication: IVIG

Primary diagnosis: Generalized myasthenia gravis (AChR antibody positive), MGFA class IIb
Secondary diagnoses: Hypertension (well controlled), GERD

Home meds:
- Pyridostigmine 60 mg PO q6h PRN
- Prednisone 10 mg PO daily
```
