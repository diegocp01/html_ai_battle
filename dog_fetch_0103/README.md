# 🧪 HTML AI Battle, HTML Animation Experiment

**TLDR:**  
4 Models try to: Dog fetching a ball animation

---

## 🎯 Original Prompt

Animate a dog fetching a ball. Using HTML/CSS/JS in a single HTML file.

---

## 📸 Results Preview

![Falling Sand simulation preview](image.png)

---

## 🤖 Per-Model Output Summary

| LLM Model                 | LLM Reasoning Time (s) | LLM Response Time (s) | Reasoning Total words | Reasoning Total characters | Reasoning Total sentences | Reasoning top keyword | Reasoning top keyword repetitions | Input Word Count | Lines of HTML | Code in Reasoning? | prompt_adherence_score (0-10) | functional_correctness_score (0-10) | ui_score (0-10) | Performance Score (0-10) |
|:------------------------|---------------------:|--------------------:|--------------------:|:-------------------------|------------------------:|:--------------------|--------------------------------:|---------------:|------------:|:-----------------|----------------------------:|----------------------------------:|--------------:|-----------------------:|
| gpt-5.2-extended-thinking |                     10 |                   116 |                    77 | 454                        |                         5 | animation             |                                 3 |               13 |           570 | n                  |                            10 |                                   9 |             8.5 |                      9.3 |
| gemini-3-pro              |                     22 |                    55 |                   616 | 3,675                      |                        42 | dog                   |                                18 |               13 |           361 | n                  |                             9 |                                   7 |               7 |                      7.8 |
| grok-4.1-thinking         |                    160 |                   167 |                   494 | 3,006                      |                        38 | ball                  |                                28 |               13 |           116 | n                  |                             8 |                                   7 |             6.5 |                      7.3 |
| opus-4.5-thinking-32k     |                      8 |                    82 |                   166 | 925                        |                         3 | ball                  |                                 9 |               13 |           615 | n                  |                           9.5 |                                   9 |             8.5 |                      9.1 |

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

• gpt-5.2-extended-thinking: Delivered a polished and interactive implementation where the dog reliably catches the ball, with a notably strong user interface and smooth overall behavior. However, the dog’s movement resembled a legless, Roomba-like glide rather than a natural run, creating an unintentionally robotic feel that undercut the otherwise high-quality presentation. Despite this visual oddity, it was a standout entry that clearly outperformed the Grok model in both functionality and execution.

• gemini-3-pro: Presented an appealing dog character with a nicely animated wagging tail, demonstrating solid attention to visual detail. Functionally, though, the experience was undermined by awkward ball behavior: each throw sent the ball off-screen, and the dog took an exaggeratedly long time to retrieve it, only to return the ball in a floating, unrealistic manner. The core concept was met, but timing and physics issues significantly diminished the practical playability.

• grok-4.1-thinking: Produced a bare-minimum, almost student-project-level implementation that did just enough to satisfy the literal requirements of the prompt. The use of emojis was a clever shortcut to represent the dog and ball, and the dog technically performed a fetch action, but the overall experience felt minimalistic and under-ambitious, with little effort invested in visuals or interaction beyond the simplest possible solution.

• opus-4.5-thinking-32k: Achieved a well-rounded and engaging result featuring a four-legged dog with a wagging tail and a responsive, interactive fetch mechanic. The animation and behavior were cohesive and visually satisfying, placing it firmly in the high-quality tier. Its main shortcoming was that the ball was always thrown to the same location, limiting variation and replay value despite the otherwise strong execution.

---

🔗 Original Post

X (Twitter) post showcasing the experiment:

Link: 

---
