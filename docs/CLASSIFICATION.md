# Document Classification Logic

## Categories

Documents are classified into one of 14 categories:

1. **Academic Notes** – Lecture notes, study guides, summaries
2. **Assignments** – Homework, coursework, individual projects
3. **Worksheets** – Practice problems, exercises, question banks
4. **Research Papers** – Academic papers, journal articles, theses
5. **Practical Files** – Lab reports, experiment data, case studies
6. **Lab Manuals** – Experiment instructions, procedures
7. **Question Papers** – Past exams, model papers, previous year questions
8. **GATE Preparation** – Graduate Aptitude Test in Engineering material
9. **Educational Books** – Textbooks, reference materials, e-books
10. **Project Reports** – Final year projects, capstone studies, dissertations
11. **Tutorials** – How-to guides, step-by-step learning
12. **Other Educational Content** – Anything academic that doesn't fit above
13. **Unrelated Content** – Non-academic documents (images, resumes, etc.)
14. **Suspicious Content** – Spam, potential malware, clearly non-academic

## Heuristic Rules (Fallback)

When no LLM is available, the classification uses these rules:

### Academic Detection

A document is considered academic if:
- It contains subject-specific keywords (CS, Math, Physics, etc.)
- It lacks suspicious keywords AND has meaningful text length (>100 chars)
- It contains study-related words: "notes", "study", "lecture", "chapter"

### Subject Detection

Subjects are detected by keyword frequency:

| Subject | Keywords |
|---------|----------|
| Computer Science | algorithm, database, SQL, python, java, data structure |
| Mathematics | calculus, derivative, integral, matrix, probability |
| Physics | Newton, force, energy, quantum, wave |
| Chemistry | reaction, molecule, compound, equation |
| Biology | cell, DNA, protein, organism |
| GATE | gate, graduate, aptitude |
| Economics | gdp, inflation, supply, demand |
| Business | management, marketing, finance |

### Document Type Detection

| Patterns | Category |
|----------|----------|
| "assignment", "homework" | Assignments |
| "worksheet", "exercise" | Worksheets |
| "research paper", "thesis" | Research Papers |
| "lab", "experiment" | Lab Manuals |
| "question paper", "exam" | Question Papers |
| "gate" | GATE Preparation |
| "textbook", "chapter" | Educational Books |
| "project report" | Project Reports |
| "tutorial", "guide" | Tutorials |
| "notes", "study" | Academic Notes |

### Confidence Calculation

```
confidence = base(50)
             - suspicious_keywords * 10
             + subject_matches * 8
             + document_type_detected * 5
```

Capped at 30-95 range.

## AI Engine Selection

| Engine | When to Use |
|--------|-------------|
| `heuristic` | No LLM available, offline mode, quick testing |
| `ollama` | Free local model, privacy important |
| `external` | Higher accuracy needed, paid API available |

## Recommendation Logic

| Confidence | Recommendation |
|------------|----------------|
| 85-100 | APPROVE_FOR_ADMIN_REVIEW |
| 60-84 | MANUAL_REVIEW_REQUIRED |
| <60 | FLAG_AS_SUSPICIOUS |

Administrators can override any recommendation.