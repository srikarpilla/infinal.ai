"""
Turns a plain text prompt into a structured video plan (JSON), using an LLM
through LangChain. We never let the LLM write HyperFrames markup directly -
it only fills in a fixed, simple schema. That schema is what the template
mapper (render_pipeline.py) reads from.
"""

import os
import json
from langchain_openai import ChatOpenAI

# Allowed animation styles. Keeping this list short is a deliberate choice -
# see the planning doc, section 3 ("fixed template set over freeform generation").
ALLOWED_STYLES = ["fade", "slide", "zoom"]

SYSTEM_PROMPT = f"""You are a motion graphics planner.

Given a short user prompt, output a JSON object describing a short video.
Return ONLY valid JSON, nothing else - no markdown fences, no explanation.

Schema:
{{
  "title": "short title text, max 6 words",
  "subtitle": "one supporting line, max 12 words",
  "style": one of {ALLOWED_STYLES},
  "duration_seconds": integer between 4 and 10,
  "background_color": a dark hex color like "#101820" (keep it dark - text is white),
  "accent_color": a bright, contrasting hex color like "#4F9DFF" used for a small
    decorative highlight - should stand out clearly against background_color
}}
"""


def get_llm():
    """Builds the LangChain LLM client, pointed at the task's custom endpoint."""
    return ChatOpenAI(
        model=os.environ["LLM_MODEL"],
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        temperature=0.4,
    )


def make_plan(prompt: str) -> dict:
    """
    Calls the LLM and returns a validated plan dict.
    Raises ValueError if the model returns something we can't use -
    we'd rather fail loudly here than pass bad data into HyperFrames.
    """
    llm = get_llm()

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])

    raw_text = response.content.strip()

    try:
        plan = json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(f"LLM did not return valid JSON:\n{raw_text}")

    # Basic validation against our schema. Simple, but this is exactly
    # the "catch it before it reaches HyperFrames" step from the design doc.
    required_keys = {"title", "subtitle", "style", "duration_seconds", "background_color"}
    missing = required_keys - plan.keys()
    if missing:
        raise ValueError(f"LLM response missing fields: {missing}")

    if plan["style"] not in ALLOWED_STYLES:
        plan["style"] = "fade"  # safe fallback instead of failing the whole request

    plan["duration_seconds"] = max(4, min(10, int(plan["duration_seconds"])))

    # accent_color is a nice-to-have, not required - fall back to a safe
    # default if the LLM left it out or returned something malformed.
    accent = plan.get("accent_color", "")
    if not isinstance(accent, str) or not accent.startswith("#") or len(accent) != 7:
        accent = "#4F9DFF"
    plan["accent_color"] = accent

    return plan
