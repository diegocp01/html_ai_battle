# 🧪 HTML AI Battle, HTML Animation Experiment

**TLDR:**  
4 Models try to: Paper airplane glide simulation using html

**Live viewer:** [Open all rendered outputs](https://gptaiacademy.com/ai-battles/html-viewer/experiments/paper_airplane_0204)

---

## 🎯 Original Prompt

Create a simulation of a paper airplane gliding through the air using HTML/CSS/JS in a single HTML file.

---

## 📸 Results Preview

![basketball preview](image.png)

---

## 🤖 Per-Model Output Summary

| LLM Model                 | Visual type | LLM Reasoning Time (s) | LLM Response Time (s) | Reasoning Total words | Reasoning Total characters | Reasoning Total sentences | Reasoning top keyword | Reasoning top keyword repetitions | Input Word Count | Lines of HTML | Platform | Code in Reasoning? | prompt_adherence_score (0-10) | functional_correctness_score (0-10) | ui_score (0-10) | Performance Score (0-10) | Song style                                                                                                                                       |
|:------------------------|:----------|---------------------:|--------------------:|:--------------------|:-------------------------|------------------------:|:--------------------|--------------------------------:|---------------:|------------:|:-------|:-----------------|----------------------------:|----------------------------------:|--------------:|-----------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------|
| gpt-5.2-extended-thinking | simple      |                     22 |                   160 | 162                   | 976                        |                        11 | airplane              |                                 5 |               18 |           711 | Web UI   | n                  |                           9.5 |                                   9 |               9 |                      9.2 | Trap, Southern hip-hop, Atlanta rap, Melodic rap, Gangsta rap, Modern hip-hop, Street rap, Drill-influenced rap, Bass-heavy rap, Minimalist trap |
| gemini-3-pro              | simple      |                     18 |                    62 | 290                   | 1,916                      |                        23 | i'm                   |                                 8 |               18 |           509 | Web UI   | n                  |                             1 |                                   0 |               4 |                      1.4 | Trap, Southern hip-hop, Atlanta rap, Melodic rap, Gangsta rap, Modern hip-hop, Street rap, Drill-influenced rap, Bass-heavy rap, Minimalist trap |
| grok-4.1-thinking         | simple      |                    123 |                   144 | 367                   | 2,376                      |                        31 | airplane              |                                 9 |               18 |           158 | Web UI   | n                  |                           9.5 |                                 9.2 |             8.5 |                      9.2 | Trap, Southern hip-hop, Atlanta rap, Melodic rap, Gangsta rap, Modern hip-hop, Street rap, Drill-influenced rap, Bass-heavy rap, Minimalist trap |
| opus-4.5-thinking-32k     | simple      |                     46 |                   118 | 1,296                 | 12,897                     |                        16 | airplane              |                                18 |               18 |           629 | LMArena  | y                  |                             7 |                                   7 |               9 |                      7.5 | Trap, Southern hip-hop, Atlanta rap, Melodic rap, Gangsta rap, Modern hip-hop, Street rap, Drill-influenced rap, Bass-heavy rap, Minimalist trap |

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

• gpt-5.2-extended-thinking: Implemented natural-looking airplane motion with user-controllable wind, though the cloud shapes appeared visually odd.
• gemini-3-pro: Produced a buggy simulation that only ran once before freezing, with the plane moving at a fixed angle instead of gliding properly.
• grok-4.1-thinking: Delivered a simple, accurate implementation of the requested simulation, with no notable issues and a straightforward design.
• opus-4.5-thinking-32k: Created an interactive drag-and-throw airplane mechanic with an initially odd circular start, enhanced by atmospheric details like small birds crossing the screen.

---

🔗 Original Post

X (Twitter) post showcasing the experiment:

Link: https://x.com/diegocabezas01/status/2019215165242151308?s=20

---
