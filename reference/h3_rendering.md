# Video model boundaries and audio strategy

Applies to H3-style image-to-video models. Verify each item on your own model —
these are empirical observations, not spec guarantees.

## Capability boundaries

| Requirement | Feasible | Evidence |
|---|---|---|
| Breathing, hair sway, light drift, eye movement | Usually | Multiple runs |
| Small mouth movement while speaking | Usually | Acceptable face stability |
| Blink / closed-eye transition | Often breaks | Eyes smear |
| Large motion (run, jump, turn, wave) | Often breaks | Rarely successful |
| Changing scene structure from prompt | No | Image conditions composition |
| Introducing characters not in the reference | No | Model invents them |
| Suppressing text/subtitles | Partial | Negative prompt lowers probability |
| Lip sync to dialogue | No | No phoneme conditioning |

## Audio strategy

Two separate jobs: **picture identity** and **voice identity**.

- Picture: lock with character reference images, every segment.
- Voice: lock with a spoken reference (`reference_audio`) once you have one clean
  line per character; describe the voice in the prompt before that.
- Ambience: reuse the **exact same wording** across segments in the same scene.
- Do not ask the model to nail both picture and voice precision in one pass; it
  degrades both.

### Voice differentiation

Describe each character's voice concretely (age, register, energy). If you can
measure, check the median F0 per segment: distinct characters should separate
clearly (e.g. child ≫ adult female > adult male). If two characters land at the
same F0, the model merged them.

Add BGM as a separate post layer; do not rely on the video model for music.

## Frame counts and resolution

- Many models align frame counts to `17n + 5` (e.g. 56, 107, 158, 362, 736) at
  fixed 24 fps. Check your provider.
- Resolution should be a multiple of 32 and close to the target aspect ratio.
- 15s ≈ 362 frames, 30s ≈ 736 frames on H3-style models. Two 15s clips give 724
  frames — a different count than a single 30s clip, which is one signal that the
  long output is generated as one sequence rather than stitched.

## Local inference notes

If you run a local build (e.g. stable-diffusion.cpp server):

- Long sequences need flash-attention on GPU architectures where the MMA path is
  available; without it, memory blows up before the sequence finishes.
- Distilled few-step LoRAs speed things up but hurt face stability; step count and
  LoRA weight need empirical tuning per model.
- Sampling parameters may use non-obvious key names (e.g. `sample_params.sample_steps`
  and `guidance.txt_cfg`). Wrong key names silently fall back to defaults.
