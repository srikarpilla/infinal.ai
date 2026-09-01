# HyperFrames Motion Graphics Generator

Prompt in, motion graphics MP4 out. See `HyperFrames_Planning_Design.docx` for
the reasoning behind this design.

## How it works

1. `planner.py` - sends your prompt to the LLM (via LangChain) and gets back
   a small structured JSON plan (title, subtitle, style, duration, color).
2. `render_pipeline.py` - fills that JSON into a HyperFrames composition
   template, then calls the HyperFrames CLI to render it to MP4.
3. `app.py` - a one-page Flask app that ties the two together.

## Setup

```bash
# 1. Install Python deps
pip install -r requirements.txt

# 2. Install HyperFrames (Node.js >= 22 and FFmpeg required)
npx hyperframes --version

# 3. Add your API key
cp .env.example .env
# then edit .env and paste your real key in

# 4. Run it
python app.py
```

Open http://localhost:5000, type a prompt, click generate.

## Notes

- The composition template in `templates/composition_template.html` is
  intentionally simple. Check it against the real HyperFrames docs
  (hyperframes.heygen.com) before relying on the exact syntax - the point
  of this file is to show how a plan maps into a composition, not to be a
  polished example of every HyperFrames feature.
- Rendering is synchronous (the request waits for the video to finish) -
  fine for a demo, not for production. See the planning doc for why.
