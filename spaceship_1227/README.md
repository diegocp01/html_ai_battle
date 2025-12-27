# 🧪 HTML AI Battle, HTML Animation Experiment

**TLDR:**  
4 Models try to: Rocket liftoff animation using html

---

## 🎯 Original Prompt

Create a rocket launch animation starting with engine ignition and heavy smoke, followed by a slow liftoff that accelerates, using HTML/CSS/JS in a single HTML file.

---

## 📸 Results Preview

![Falling Sand simulation preview](image.png)

---

## 🤖 Per-Model Output Summary

| LLM Model                 | LLM Reasoning Time (s) | LLM Response Time (s) | Reasoning Total words | Reasoning Total characters | Reasoning Total sentences | Reasoning top keyword | Reasoning top keyword repetitions | Input Word Count | Lines of HTML | Code in Reasoning? | prompt_adherence_score (0-10) | functional_correctness_score (0-10) | ui_score (0-10) | Performance Score (0-10) |
|:------------------------|---------------------:|--------------------:|:--------------------|:-------------------------|------------------------:|:--------------------|--------------------------------:|---------------:|------------:|:-----------------|----------------------------:|----------------------------------:|--------------:|-----------------------:|
| gpt-5.2-extended-thinking |                     22 |                   129 | 205                   | 1,299                      |                        13 | rocket                |                                 7 |               26 |           618 | n                  |                           9.5 |                                 9.5 |              10 |                      9.6 |
| gemini-3-pro              |                     10 |                    36 | 203                   | 1,281                      |                        14 | i'm                   |                                 9 |               26 |           332 | n                  |                             9 |                                   9 |               9 |                        9 |
| grok-4.1-thinking         |                      6 |                    10 | 63                    | 426                        |                         4 | smoke                 |                                 3 |               26 |           188 | n                  |                             3 |                                   3 |               2 |                      2.8 |
| opus-4.5-thinking-32k     |                     72 |                   184 | 1,353                 | 13,922                     |                        16 | 50%                   |                                23 |               26 |           820 | y                  |                             7 |                                   7 |             8.5 |                      7.4 |

---

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

• gpt-5.2-extended-thinking: Delivered an impressively polished implementation that aligned closely with the prompt. The interface was visually appealing and responsive, featuring a subtle but effective screen shake on launch that enhanced the sense of power and motion. The overall execution was focused, clean, and technically solid, resulting in a standout animation that felt both complete and satisfying to watch.

• gemini-3-pro: Produced a clean, straightforward solution that executed the core requirements effectively. The rocket animation, smoke effects, and liftoff sequence were all handled with care, resulting in a smooth and convincing launch. While the approach favored simplicity over flourishes, the fundamentals were executed so well that the overall result felt robust and reliable.

• grok-4.1-thinking: Failed to meet the essential visual and behavioral expectations of the prompt. The rocket design was overly abstract—resembled more a simple triangle than a recognizable vehicle—and the absence of smoke severely undermined the intended launch sequence. The resulting animation felt odd and unconvincing, reflecting an over-simplified approach that compromised both realism and fidelity to the task.

• opus-4.5-thinking-32k: Presented a visually attractive interface with a well-crafted, detailed rocket and a thoughtful addition of a 10-second countdown timer—an exclusive feature among the models tested. However, the core requirement of showing the actual launch animation was effectively missed, as the liftoff was not visible. The lack of smoke further weakened the illusion of a realistic launch, leaving a polished but incomplete experience.

---

🔗 Original Post

X (Twitter) post showcasing the experiment:

Link: https://x.com/diegocabezas01/status/2004908584656617578?s=20

---
