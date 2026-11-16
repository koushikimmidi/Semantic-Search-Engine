# Using the engine in different sectors

The engine answers from whatever documents it is given, so moving it to a new sector is mostly a
content task: collect the documents people already use to answer questions, describe the main
question types, and set how cautious automatic replies should be.

Every sector follows the same four steps:

1. **Documents** — put the policies, FAQs, procedures and guides in a folder and point
   `KNOWLEDGE_BASE_PATH` at it (or upload them in **Knowledge base**).
2. **Intents** — list 10–15 example questions per question type in
   `data/intent/intent_examples.json`, plus an `OUT_OF_SCOPE` list.
3. **Evaluate** — write 50–100 real questions into `data/eval/eval_set.json` and run
   `python -m scripts.evaluate_pipeline --full`.
4. **Tune caution** — raise the `CONFIDENCE_*` thresholds in `.env` for sensitive sectors, so more
   questions go to a person.

---

## 🎓 Education

**Takes over:** admissions and eligibility, fee and refund policy, course access, certificates,
exam and timetable questions, LMS and password support.

**Documents:** prospectus, fee and refund policy, academic calendar, certificate policy, LMS help
pages, hostel and transport rules.

**Intents to start with:** `ADMISSIONS`, `FEES_REFUND`, `COURSE_ACCESS`, `CERTIFICATE`, `EXAMS`,
`ACCOUNT_LOGIN`, `TECHNICAL_SUPPORT`.

**Caution level:** standard. This repository ships with an education knowledge base and the
default thresholds.

## 🏥 Healthcare (administrative)

**Takes over:** appointment booking and rescheduling, clinic timings and locations, doctor
availability, insurance and billing, pre-visit instructions, lab-report collection.

**Documents:** front-office procedures, department directory, insurance and billing policy,
preparation instructions for tests, visiting rules.

**Intents to start with:** `APPOINTMENT`, `TIMINGS_LOCATION`, `BILLING_INSURANCE`,
`TEST_PREPARATION`, `REPORTS`, plus a strict `MEDICAL_ADVICE` intent that always routes to a person.

**Caution level:** high. Raise `CONFIDENCE_VERY_HIGH_THRESHOLD`, add symptom and medication
questions to `OUT_OF_SCOPE`, and keep automatic replies to administrative topics only. The engine
must not be used for diagnosis or treatment advice.

## 🏦 Banking and finance

**Takes over:** card blocking steps, account-opening documents, KYC requirements, charges and
limits, loan eligibility criteria, statement and certificate requests, branch timings.

**Documents:** schedule of charges, KYC policy, product terms, loan eligibility guides, card
services procedures, grievance policy.

**Intents to start with:** `CARD_SERVICES`, `ACCOUNT_OPENING`, `KYC`, `CHARGES_LIMITS`, `LOANS`,
`STATEMENTS`, `FRAUD_REPORT` (always to a person).

**Caution level:** high. Never answer account-specific questions (balances, transactions) from
documents; route them to staff. Run the system inside the bank's network — the LLM is local, so no
customer text leaves it.

## 🛒 E-commerce and retail

**Takes over:** order status steps, return and refund policy, delivery times, warranty terms,
payment issues, size and product FAQs.

**Documents:** returns policy, shipping policy, warranty terms, payment FAQ, product guides.

**Intents to start with:** `ORDER_STATUS`, `RETURNS_REFUNDS`, `DELIVERY`, `WARRANTY`, `PAYMENT`,
`PRODUCT_INFO`.

**Caution level:** standard. High volumes make automatic replies especially valuable here.

## 📡 Telecom and utilities

**Takes over:** plan details and recharges, bill explanations, outage information, new connection
and transfer procedures, device setup guides.

**Documents:** tariff sheets, billing FAQ, connection procedures, troubleshooting guides.

**Intents to start with:** `PLANS_RECHARGE`, `BILLING`, `OUTAGE`, `NEW_CONNECTION`,
`DEVICE_SETUP`.

## 🛡️ Insurance

**Takes over:** coverage explanations, claim procedures and required documents, renewal steps,
premium payment options.

**Documents:** policy wordings, claim procedure guides, document checklists, renewal FAQ.

**Intents to start with:** `COVERAGE`, `CLAIM_PROCESS`, `DOCUMENTS`, `RENEWAL`, `PAYMENT`.

**Caution level:** high for coverage decisions — answer *how* to claim automatically, but route
*whether a specific claim is covered* to a person.

## 🏛️ Government and public services

**Takes over:** application procedures, eligibility criteria, required documents, fees, office
hours, application-status steps.

**Documents:** citizen charters, scheme guidelines, application manuals, fee schedules.

**Intents to start with:** `ELIGIBILITY`, `HOW_TO_APPLY`, `DOCUMENTS_REQUIRED`, `FEES`,
`OFFICE_INFO`, `STATUS`.

## 🏢 HR and internal IT help desks

**Takes over:** leave and attendance policy, payroll and reimbursement rules, onboarding steps,
password resets, VPN and software access, equipment requests.

**Documents:** employee handbook, leave policy, reimbursement policy, IT how-to guides.

**Intents to start with:** `LEAVE`, `PAYROLL`, `REIMBURSEMENT`, `ONBOARDING`, `PASSWORD_ACCESS`,
`SOFTWARE_REQUEST`.

**Caution level:** standard; route anything about an individual's pay or performance to HR.

---

## Measuring the impact

The **Analytics** page shows, for any period:

- **Answered automatically** — the share of questions that needed no person at all.
- **Waiting for review** and **time to resolve** — how quickly the team handles the rest.
- **Knowledge gaps** — questions the documents could not answer. Adding a document for the most
  frequent gap is usually the single biggest improvement.

A practical rollout: run with automatic replies **off** for two weeks, review the drafts in the
review queue, add documents for the gaps, re-run the evaluation, then turn automatic replies on.
