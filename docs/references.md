# Citations to use — the focused shortlist

**Principle:** The paper's References section is lean and earned, not a literature dump. This shortlist is the ~30 papers we actually cite across the paper and the dataset documentation (dataset card, datasheet, data statement, taxonomy reference).

---

## A. ABA × NLP — direct predecessors and positioning (6)

1. **Kumar, A., et al. (2024). Personalized-ABA.** *NLP4Science @ ACL.* https://aclanthology.org/2024.nlp4science-1.16/
   *How we cite:* direct predecessor; benchmark to beat.

2. **Cox, D. J., & Jennings, A. M. (2024). Promises and possibilities of AI in behavior analytic services.** *Behavior Analysis in Practice, 17*, 123–136. https://pmc.ncbi.nlm.nih.gov/articles/PMC10890993/
   *How we cite:* motivates the application space, especially "NLP on session notes."

3. **Jennings, A. M., & Cox, D. J. (2024). Starting the conversation around the ethical use of AI in ABA.** *Behavior Analysis in Practice, 17*, 107–122. https://pmc.ncbi.nlm.nih.gov/articles/PMC10891004/
   *How we cite:* ethics spine — BACB 2.03/2.05, HIPAA, explainability criteria our stack satisfies by construction.

4. **Peck, S., O'Brien, C., Bourret, J., & Agostinelli, D. (2025). ChatGPT versus clinician responses to questions in ABA.** *JABA.* https://onlinelibrary.wiley.com/doi/10.1002/jaba.70029
   *How we cite:* BCBAs already prefer LLMs blind — raises hallucination stakes.

5. **Garg, M., Raza, S., Rayana, S., Liu, X., & Sohn, S. (2025). The rise of small language models in healthcare: A comprehensive survey.** arXiv:2504.17119. https://arxiv.org/abs/2504.17119
   *How we cite:* positions our work in SLM-clinical field; ABA is a named white-space in their taxonomy.

6. **Gao, L. et al. (2025). Generative AI for assessment and treatment of autism spectrum disorders: A scoping review.** *Frontiers in Psychiatry.* https://pmc.ncbi.nlm.nih.gov/articles/PMC12322814/
   *How we cite:* none of the 10 studies surveyed cover BCBA workflow / session logs / on-device — directly positions our contribution.

## B. Stack precedents — small clinical on-device LMs (3)

7. **Zhang, T., et al. (2025). Menta: On-device SLM for mental health.** arXiv:2512.02716. https://arxiv.org/abs/2512.02716
   *How we cite:* direct recipe precedent (4B + LoRA r=16 α=32 + 4-bit on iPhone, beats 13B).

8. **MedGemma Team, Google DeepMind (2025). MedGemma Technical Report.** arXiv:2507.05201. https://arxiv.org/abs/2507.05201
   *How we cite:* Gemma family at 4B is clinically competent — direct stack-choice precedent.

9. **Dettmers, T., et al. (2023). QLoRA: Efficient Finetuning of Quantized LLMs.** *NeurIPS.* https://arxiv.org/abs/2305.14314
   *How we cite:* foundational method for our QLoRA fine-tuning.

## C. Data methodology (4)

10. **Wang, Y., et al. (2023). Self-Instruct.** *ACL.* https://arxiv.org/abs/2212.10560
    *How we cite:* foundational instruction-bootstrapping pipeline; source of ROUGE-L<0.7 dedup.

11. **Zhang, X., et al. (2023). AlpaCare.** arXiv:2310.14558. https://arxiv.org/abs/2310.14558
    *How we cite:* clinician-seeded stratification recipe — the key quality lever for medical instruction tuning.

12. **Gekhman, Z., et al. (2024). Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?** *EMNLP.* https://arxiv.org/abs/2405.05904
    *How we cite:* grounds our "teach format, not new facts" design.

13. **Patel, M., et al. (2025). How to Design, Create, and Evaluate an Instruction-Tuning Dataset in Health Care.** *JMIR.* https://www.jmir.org/2025/1/e70481
    *How we cite:* our validation protocol (4-dim rubric, κ with cooldown) follows this tutorial directly.

## D. Evaluation methodology (7)

14. **Singhal, K., et al. (2025). Toward expert-level medical question answering with LLMs (Med-PaLM 2).** *Nature Medicine.* https://www.nature.com/articles/s41591-024-03423-7
    *How we cite:* rubric design (9 axes, pairwise ranking) — the clinical-NLG gold standard.

15. **Arora, R. K., et al. (2025). HealthBench.** arXiv:2505.08775. https://arxiv.org/abs/2505.08775
    *How we cite:* justifies our 3-point rubric scale over Likert-5/7.

16. **Kim, S., et al. (2024). Prometheus 2.** arXiv:2405.01535. https://arxiv.org/abs/2405.01535
    *How we cite:* the open, local LLM judge we run alongside GPT-4.1 and Claude.

17. **Zheng, L., et al. (2024). Judging LLM-as-a-Judge (MT-Bench).** *NeurIPS 2023.* https://arxiv.org/abs/2306.05685
    *How we cite:* sources of position / verbosity / self-enhancement bias; justifies our swap-augmentation and panel diversity.

18. **Kulkarni et al. (2025). TN-Eval: Behavioral therapy note rubrics.** arXiv:2503.20648. https://arxiv.org/abs/2503.20648
    *How we cite:* closest adjacent rubric; faithfulness warning (therapists preferred hallucinated notes).

19. **Manakul, P., et al. (2023). SelfCheckGPT.** arXiv:2303.08896. https://arxiv.org/abs/2303.08896
    *How we cite:* our zero-resource hallucination metric.

20. **Reiter, E. (2018). A Structured Review of the Validity of BLEU.** *Computational Linguistics, 44*(3), 393–401. https://direct.mit.edu/coli/article/44/3/393/
    *How we cite:* justifies NOT using BLEU as a primary metric (negation matters in evaluation claims).

## E. Statistical grounding (3)

21. **Cohen, J. (1968). Weighted kappa.** *Psychological Bulletin, 70*(4).
    *How we cite:* quadratic-weighted κ for our ordinal escalation-level classifier.

22. **Chicco, D., & Jurman, G. (2020). Advantages of MCC over F1 and accuracy.** *BMC Genomics.* https://link.springer.com/article/10.1186/s12864-019-6413-7
    *How we cite:* justifies reporting MCC alongside macro-F1 on imbalanced classification heads.

23. **Guo, C., et al. (2017). On Calibration of Modern Neural Networks.** *ICML.* https://arxiv.org/abs/1706.04599
    *How we cite:* source of ECE + temperature-scaling for our confidence calibration.

## F. ABA foundation (5)

24. **Cooper, J. O., Heron, T. E., & Heward, W. L. (2020). *Applied Behavior Analysis* (3rd ed.).** Pearson. ISBN 978-0134752556.
    *How we cite:* canonical ABA reference — chapter citations for DTT, task analysis, measurement, IOA, FBA, BIP components.

25. **Iwata, B. A., Dorsey, M. F., Slifer, K. J., Bauman, K. E., & Richman, G. S. (1982/1994). Toward a functional analysis of self-injury.** *JABA, 27*(2), 197–209. https://doi.org/10.1901/jaba.1994.27-197
    *How we cite:* bedrock of the four-function taxonomy we encode.

26. **Carr, E. G., & Durand, V. M. (1985). Reducing behavior problems through functional communication training.** *JABA, 18*(2), 111–126. https://doi.org/10.1901/jaba.1985.18-111
    *How we cite:* origin of FCT; replacement-behavior framework.

27. **Hanley, G. P., Iwata, B. A., & McCord, B. E. (2003). Functional analysis of problem behavior: A review.** *JABA, 36*(2), 147–185. https://doi.org/10.1901/jaba.2003.36-147
    *How we cite:* definitive FBA review, finalization of four-function taxonomy.

28. **Lovaas, O. I. (1987). Behavioral treatment and normal educational and intellectual functioning in young autistic children.** *JCCP, 55*(1), 3–9. https://doi.org/10.1037/0022-006X.55.1.3
    *How we cite:* DTT / EIBI historical origin.

## G. Dataset documentation (2)

29. **Gebru, T., et al. (2021). Datasheets for Datasets.** *CACM.* https://arxiv.org/abs/1803.09010
    *How we cite:* template for our dataset's datasheet appendix.

30. **Bender, E., & Friedman, B. (2018). Data Statements for NLP.** *TACL.* https://aclanthology.org/Q18-1041/
    *How we cite:* NLP-specific data disclosure — complements Gebru datasheet.

---

## What was intentionally dropped (and why)

Comprehensive background is in `literature-foundation.md`. The following categories do **not** earn spots in the paper's References:

- **Target-behavior JABA papers** (Kodak elopement, Piazza pica, Marcus aggression, Rapp & Vollmer stereotypy, etc.) — These ground the dataset's operational definitions and belong in the **dataset card / datasheet**, not the main paper. They'll appear in a supplementary `taxonomy-v1.md`.
- **Curriculum primary sources beyond VB-MAPP** (AFLS, ABLLS-R, Essential for Living, PEAK) — cite only if we actually use them as data sources. Current pipeline uses VB-MAPP only; others stay in background reading.
- **Secondary synthetic-data papers** (phi-1, Orca, LIMA, Baize, MedAlpaca, Clinical Camel, Persona Hub, Evol-Instruct, LAB, DataDreamer) — Self-Instruct + AlpaCare + Gekhman + Patel cover our method grounding. The rest are design inspiration, not required citations.
- **Secondary evaluation papers** (GPTScore, JudgeLM, BARTScore, Med-HALT, MedHallu, HELM critiques, Abacha MEDIQA, G-Eval) — Prometheus 2 + MT-Bench + TN-Eval + SelfCheckGPT + Reiter + Med-PaLM 2 cover our method grounding.
- **Older measurement / IOA JABA papers** (Powell 1975, Harrop & Daniels 1986, Kazdin 1977) — covered by Cooper/Heron/Heward textbook chapters.
- **Teaching-method origins beyond DTT** (Hart & Risley 1975 NET, Koegel 1987 PRT, Parsons 2012 BST, Tiger 2008 FCT review, Slocum & Tiger 2011 chaining) — covered by CHH textbook chapter citations. Only cite these JABA papers individually if our paper makes a specific claim about that teaching method.
- **Neuromnia blog / Meta-AI press** — not citable in an academic venue; mention in passing without reference.
- **Lanovaz & Hranchuk 2021** — different task (visual-inspection binary classification from graphs); only cite if we explicitly contrast against it. Likely drop.
- **Dataset documentation meta-papers** (Bender 2023 Data Statements v2, HF dataset card docs, NeurIPS 2025 D&B CfP, Giuffrè 2023 synthetic health, Pezoulas 2025 privacy, Mozilla/AI-Alliance 2024) — cite only where directly relevant in the datasheet, not in the main paper.

---

## Summary

| Category | Count |
|---|---|
| ABA × NLP | 6 |
| Stack precedents | 3 |
| Data methodology | 4 |
| Evaluation methodology | 7 |
| Statistical grounding | 3 |
| ABA foundation | 5 |
| Dataset documentation | 2 |
| **Total** | **30** |

Appropriate for a 4-page ACL paper (typical range 20–40 citations) plus a NeurIPS D&B dataset paper appendix. Add more only when the text actually needs them.
