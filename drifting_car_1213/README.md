# 🧪 HTML AI Battle, HTML Animation Experiment

**TLDR:**  
4 Models try to: Create 3D drifting F1 donut simulation

---

## 🎯 Original Prompt

Create a 3D simulation of a formula 1 car performing a continuous drifting donut in the street using HTML/CSS/JS in a single HTML file. 


---

## 📸 Results Preview

![Falling Sand simulation preview](image.png)

---

## 🤖 Per-Model Output Summary

| LLM Model                | LLM Reasoning Time (s) | LLM Response Time (s) | LLM Total words | Reasoning Total characters | Reasoning Total sentences | Reasoning top keyword | Reasoning top keyword repetitions | Input Word Count | Lines of HTML | Code in Reasoning? | prompt_adherence_score (0–10) | functional_correctness_score (0–10) | ui_score (0–10) | Performance Score (0–10) |
|--------------------------|-----------------------:|----------------------:|----------------:|---------------------------:|---------------------------:|----------------------|----------------------------------:|-----------------:|--------------:|--------------------|-------------------------------:|------------------------------------:|----------------:|--------------------------:|
| gpt-5.2-extended-thinking | 23                    | 102                   | 229             | 1,374                      | 16                         | Will                 | 8                                 | 24               | 640           | n                  | 0.0                            | 0.0                                 | 1.0             | 0.3                       |
| gemini-3-pro             | 13                    | 43                    | 220             | 1,347                      | 14                         | Will                 | 6                                 | 24               | 282           | n                  | 9.0                            | 9.0                                 | 8.0             | 8.8                       |
| grok-4.1-thinking        | 8                     | 15                    | 72              | 431                        | 4                          | Request              | 2                                 | 24               | 151           | n                  | 1.0                            | 1.0                                 | 1.0             | 1.0                       |
| opus-4.5-thinking-32k    | 57                    | 173                   | 1,297           | 12,524                     | 24                         | Const                | 45                                | 24               | 682           | y                  | 10.0                           | 10.0                                | 10.0            | 10.0                      |


## Weighted Performance Score
A single score that combines how well the model follows the prompt, how correctly the code works, and how good the UI looks.  
**performance_score = 0.40(prompt_adherence_score) + 0.35(functional_correctness_score) + 0.25(ui_score)**


---

## ✅ Experiment Rules
	•	✅ Same exact prompt for all models
	•	✅ First output only (no retries, no iterations)
	•	✅ Raw HTML outputs preserved exactly
	•	✅ No human edits

---

## 🧠 Observations
• gpt-5.2-extended-thinking: Failed to produce a functional simulation. The output focused primarily on textual or parameter-based elements rather than motion or physical behavior. No meaningful drifting or animation was observed. Overall prompt adherence was low, resulting in a minimal and ineffective implementation.

• gemini-3-pro: Successfully rendered a drifting scenario with a clear Drift style motion. While the overall execution was strong, the front tire behavior appeared visually inconsistent, slightly detracting from realism. Despite this, the motion and scene composition remained coherent and engaging.

• grok-4.1-thinking: Rendered a visible scene, but physics execution was incorrect. The vehicle appeared to float vertically, and the intended drifting behavior was replaced by camera movement rather than object motion. Functional rendering was achieved, but physical realism and prompt adherence were weak.

• opus-4.5-thinking-32k: Outstanding execution across motion, interactivity, and physics. The drifting behavior was correctly implemented, interactive elements were present, and the simulation demonstrated high fidelity and realism. This model delivered the most complete and polished result, significantly outperforming the others.

---

🔗 Original Post

X (Twitter) post showcasing the experiment:

Link: https://x.com/diegocabezas01/status/1999825601604002211?s=20

---
