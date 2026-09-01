"""
Takes a plan dict (from planner.py) and turns it into an actual MP4 by:
  1. filling the plan into a HyperFrames composition file (templates/)
  2. calling the HyperFrames CLI to render that composition to video

This is a plain function, not a class - there's only one linear path
through it, so extra structure would just be noise. See the design doc,
section 4, for why this is synchronous rather than a background job.
"""

import os
import sys
import json
import uuid
import subprocess
from jinja2 import Environment, FileSystemLoader

# On Windows, "npx" is actually "npx.cmd" - subprocess.run can't find plain
# "npx" the way it can on Linux/Mac, so we pick the right name per platform.
NPX_COMMAND = "npx.cmd" if sys.platform == "win32" else "npx"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

jinja_env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")))


def write_project_config(work_dir: str) -> None:
    """
    Writes a minimal hyperframes.json into work_dir. The scaffolded example
    project had one alongside index.html, so we include a bare-bones version
    here too rather than assume the CLI works fine without it.
    """
    config = {
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {
            "blocks": "compositions",
            "components": "compositions/components",
            "assets": "assets",
        },
    }
    with open(os.path.join(work_dir, "hyperframes.json"), "w") as f:
        json.dump(config, f, indent=2)


def build_composition(plan: dict, work_dir: str) -> str:
    """Fills the plan into the HTML template and writes index.html into work_dir."""
    write_project_config(work_dir)

    template = jinja_env.get_template("composition_template.html")
    html = template.render(**plan)

    composition_path = os.path.join(work_dir, "index.html")
    with open(composition_path, "w") as f:
        f.write(html)

    return composition_path


def render_video(work_dir: str, output_path: str) -> None:
    """
    Shells out to the HyperFrames CLI to render the composition in work_dir
    to an MP4 at output_path.

    We pass a full copy of the current environment plus HYPERFRAMES_BROWSER_PATH
    (if set in .env) explicitly, so the fix for the Windows Chromium crash
    applies every time the app runs this - not just when someone remembers
    to "set" it manually in the terminal first.
    """
    render_env = os.environ.copy()

    result = subprocess.run(
        [NPX_COMMAND, "hyperframes", "render", work_dir, "-o", output_path],
        capture_output=True,
        text=True,
        env=render_env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"HyperFrames render failed:\n{result.stderr}")


def generate_video(plan: dict) -> str:
    """
    Full pipeline: plan -> composition file -> rendered MP4.
    Returns the path to the finished video file.
    """
    job_id = uuid.uuid4().hex[:8]
    work_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)

    build_composition(plan, work_dir)

    output_path = os.path.join(work_dir, "video.mp4")
    render_video(work_dir, output_path)

    return output_path
