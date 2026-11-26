# Personal presentation: under-two-minute target

Current English alternative to [the Chinese two-minute script](PERSONAL_TALK_2MIN_ZH.md), not an extra segment. Estimated timing depends on speech rate and pauses; rehearse with a timer. No new experiments are introduced. All three references are linked in the Chinese script.

My direction was to improve hypothesis coverage through parameter training.

HypoSpace shows that valid generation can still concentrate on a few hypotheses. GAPO studies diversity through group-level reinforcement-learning rewards. Building on that motivation, I explored a task-specific supervised coverage objective.

I grouped verified answers using HypoSpace's structural rules, summed two answer-form probabilities per class, and used a sixteen-draw hit probability as a coverage surrogate. I combined it with balanced SFT and trained LoRA adapters on a 1.5-billion-parameter Qwen model on my Mac.

I compared five methods on twenty-six test observation sets with three inference seeds, keeping fine-tuning data and budgets matched.

Recovery increased from 13.67 percent for the base model to 37.76 percent. However, balanced SFT already reached 36.86 percent, so the extra recovery benefit remains uncertain. Exploratory analysis showed higher validity, accompanied by lower structural uniqueness.

My completed contribution is the task-specific objective, matched ablations, and a reproducible implementation, with conclusions limited to this small Boolean study.

Keep the matched-SFT result and uncertainty when shortening. Three inference seeds are not three training runs. The methodological contribution is the task-specific coverage objective; LoRA and the prior group-diversity idea are credited existing work.
