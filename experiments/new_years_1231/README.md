# 🧪 HTML AI Battle, HTML Animation Experiment

**TLDR:**  
4 Models try to: Interactive New Year's fireworks with finale html

---

## 🎯 Original Prompt

Create an interactive New Year's Eve fireworks display using HTML/CSS/JS in a single HTML file. When the user clicks, a rocket should launch and explode into colorful particles with gravity and drag physics. Include a 'Grand Finale' button that automatically launches a barrage of fireworks that form the glowing text 'HELLO 2026' in the sky.

---

## 📸 Results Preview

![Falling Sand simulation preview](image.png)

---

## 🤖 Per-Model Output Summary

| LLM Model                 | LLM Reasoning Time (s) | LLM Response Time (s) | Reasoning Total words | Reasoning Total characters | Reasoning Total sentences | Reasoning top keyword | Reasoning top keyword repetitions | Input Word Count | Lines of HTML | Code in Reasoning? | prompt_adherence_score (0-10) | functional_correctness_score (0-10) | ui_score (0-10) | Performance Score (0-10) |
|:------------------------|---------------------:|--------------------:|:--------------------|:-------------------------|------------------------:|:--------------------|--------------------------------:|---------------:|------------:|:-----------------|----------------------------:|----------------------------------:|--------------:|-----------------------:|
| gpt-5.2-extended-thinking |                     36 |                   180 | 259                   | 1,698                      |                        14 | particles             |                                11 |               55 |           758 | n                  |                           9.5 |                                 9.5 |             9.5 |                      9.5 |
| gemini-3-pro              |                     19 |                    48 | 435                   | 2,813                      |                        31 | i'm                   |                                10 |               55 |           380 | n                  |                             8 |                                   8 |             8.5 |                      8.1 |
| grok-4.1-thinking         |                    170 |                   224 | 301                   | 2,031                      |                        27 | explosion             |                                 8 |               55 |           241 | n                  |                             6 |                                   7 |               7 |                      6.6 |
| opus-4.5-thinking-32k     |                     80 |                   175 | 1,600                 | 14,221                     |                        33 | thisy                 |                                17 |               55 |           608 | y                  |                             7 |                                   7 |               9 |                      7.5 |

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

• gpt-5.2-extended-thinking: Delivered an impressive and highly polished implementation where rockets reliably launch on click and the Grand Finale sequence successfully renders a clear “HELLO 2026” in the sky. The main shortcoming is timing: the celebratory text disappears in under a second, making it difficult to fully appreciate the effect. Despite this fleeting display, the overall execution was strong enough to stand out as a top performer in this test.

• gemini-3-pro: Produced a mostly functional display with mixed reliability in the core fireworks behavior. Some rockets explode as intended, while others simply exit the screen without detonating, creating an inconsistent experience. During the Grand Finale, “HELLO 2026” appears and lingers on screen, but the text is not formed by the explosions themselves, diverging from the prompt’s requirements. The result is visually acceptable yet structurally incomplete in terms of the specified interaction between fireworks and text formation.

• grok-4.1-thinking: Implemented an appealing rocket effect that initially shows promise but suffers from a major behavioral flaw: the majority of rockets never explode within the visible frame and instead travel upward indefinitely. The Grand Finale further weakens the experience, presenting a slow, dated-feeling sequence that fails to form the requested “HELLO 2026” text. While the visual concept has potential, the combination of off-screen explosions and an underwhelming finale significantly reduces its overall effectiveness.

• opus-4.5-thinking-32k: Started exceptionally strong with responsive, visually impressive rockets that explode cleanly within the screen bounds, clearly surpassing the others in feel and presentation. The countdown to the Grand Finale added a dramatic, well-executed buildup that suggested a near-perfect solution. However, the final sequence does not actually assemble the “HELLO 2026” text as required, falling just short of complete compliance with the prompt. The result is a highly polished and engaging display that narrowly misses top marks due to this critical omission.

---

🔗 Original Post

X (Twitter) post showcasing the experiment:

Link: https://x.com/diegocabezas01/status/2006340874104353078?s=20

---
