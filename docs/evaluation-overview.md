# LLM Triple Extraction — Evaluation Overview

**Goal:** Can a Large Language Model (LLM) replace hand-coded scraping rules when extracting product facts from Amazon pages?

---

## What Is a Triple?

A **triple** is a single structured fact about a product, expressed as three parts:

```
(product name)  --[relationship]-->  (value)

e.g. "Google Nest Thermostat"  --[manufacturedBy]-->  "Google"
     "Google Nest Thermostat"  --[hasConnectivity]-->  "Wi-Fi"
```

The goal of both approaches is to extract as many of these triples as possible from a product page.

---

## The Two Approaches

### Template Extractor — The Rulebook
A hand-coded program that reads Amazon's page layout and pulls facts from known locations (brand field, spec tables, bullet points, etc.). It always produces the same output for the same page. **This is our reference — what we expect the LLM to match.**

### LLM Extractor — The AI
A local AI model that reads the same page text and extracts triples based on understanding language. It has no hard-coded rules — just instructions and the page content.

---

## How We Evaluate

We run both approaches on the same product page and compare their outputs.

| Result | Meaning |
|---|---|
| **Match (True Positive)** | LLM found the same fact as the template |
| **Missed (False Negative)** | Template found it, LLM didn't — a gap in the LLM |
| **Extra (False Positive)** | LLM found it, template didn't — needs human review |

From these we calculate three scores:

- **Recall** — what fraction of the template's facts did the LLM find? *(Most important for replacement)*
- **Precision** — of what the LLM produced, how much was correct?
- **F1** — a single combined score balancing both

---

## Why Human Review Matters

When the LLM finds something the template didn't, we can't automatically tell whether it:

- **Made it up** (hallucination — bad), or
- **Found a real fact the template missed** (good — suggests the template has gaps)

A human reviewer labels each of these cases. Until that's done, our precision score is conservative by design.

---

## Output

Every evaluation run produces:
- A **terminal report** showing matched facts, misses, and extras
- A **JSON file** saved to `data/evaluation/` with full detail for human review

---

## Key Design Choice

Matching is **exact** — the LLM must use the same relationship names and copy values word-for-word from the page. This is intentional: it keeps the evaluation clean and ensures any mismatch reflects a real failure, not a formatting difference.

### Evaluation vs. Pipeline — Two Different Prompts

It is important to note that the LLM is given **different instructions** depending on context:

| | Evaluation | Production Pipeline |
|---|---|---|
| **Goal** | Measure how well the LLM replicates the template | Build the actual knowledge graph |
| **Value instruction** | Copy values exactly as they appear on the page | No strict verbatim requirement |
| **Expected behavior** | Preserve full, raw text | May summarize or clean up values naturally |

The template extractor stores the full product title as-is:

```
"Google Nest Thermostat - Smart Thermostat for Home - Programmable Wifi Thermostat - Snow"
```

Without the verbatim instruction, the LLM naturally shortens this to:

```
"Google Nest Thermostat"
```

Neither is wrong in isolation — but they won't match under exact comparison, which is exactly why the evaluation prompt explicitly requires verbatim values. Without that constraint, the LLM's natural tendency to clean up text would register as failures, making the evaluation misleading.
