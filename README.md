# SemiShape

> **"Almost a shape. Mostly suggestion."**

![Status](https://img.shields.io/badge/Status-Pre--Alpha_v0.1.0-orange)
![License](https://img.shields.io/badge/License-Apache_2.0-blue)
![Framework](https://img.shields.io/badge/Powered_by-build123d_v0.10.0-green)

SemiShape is an experimental AI-assisted co-pilot designed for the [build123d](https://github.com/gumyr/build123d) Python CAD library. It represents a practical application of my ongoing learning journey in AI Engineering and Parametric Design.

## Live Access

The experimental assistant is accessible directly via Google AI Studio:  
**[Launch SemiShape on Google AI Studio](https://ai.studio/apps/drive/11MgLYenkh66Y4qcUufuT2tAvfxitxLz1?fullscreenApplet=true)**

---

## Context and Motivation

This project is a functional bridge within my self-study ecosystem, connecting two of my primary repositories:

1. **AI Workshop**: Structured learning of Python foundations and Generative AI implementation.
2. **CAD Workshop**: Transitioning from traditional GUI-based CAD to a "Code-first" approach for superior maintainability and version control.

SemiShape was developed to automate the boilerplate code required in parametric modeling while strictly adhering to the engineering standards of the OCCT (Open Cascade) kernel.

### Technical Genesis

SemiShape was developed entirely within **Google AI Studio**. By leveraging Generative AI, I translated high-level mechanical design requirements into functional application logic. This project serves as a proof-of-concept for AI-driven software development, demonstrating how a self-taught enthusiast can build complex CAD tools by combining structured learning with advanced LLM prompting.

### Future Vision

As part of my broader AI Engineering roadmap, I view SemiShape as a long-term testing ground. The ultimate aspirational milestone is to move beyond basic prompting by integrating **RAG (Retrieval-Augmented Generation) via Dify**.

By implementig a **Knowledge Pipeline with vectorized build123d documentation**, the assistant will be able to perform surgical retrieval of exact documentation snippets. This approach is designed to:

- **Optimize context window usage** (significant token savings compared to long-context prompting).
- **Increase code precision** by providing the LLM with real-time, authoritative documentation.
- **Minimize hallucinations** caused by legacy training data.

While this evolution represents a journey of potentially several months or years of study, it remains the "North Star" for this experiment.

## Core Philosophy

SemiShape operates on a "Pilot and Co-pilot" principle:

| Role              | Responsibility                                                                  |
| ----------------- | ------------------------------------------------------------------------------- |
| **User (Pilot)**  | Defines physical intent, engineering constraints, and verifies geometry.        |
| **AI (Co-pilot)** | Proposes code structure, handles syntax nuances, and suggests robust selectors. |

## Key Technical Features

- **Strict Parametrization**: All dimensions are defined as variables to ensure models are truly parametric and easily refactored.
- **Modern Syntax Enforcement**: Prioritizes `with BuildPart()` context managers and 2D-sketch-first workflows.
- **Selector Stability**: Recommends geometric selectors (e.g., `.sort_by(Axis.Z)`) and `Select.LAST` instead of fragile index-based selections.
- **Workflow Integration**: Optimized for local execution and 3D visualization within VS Code using OCP CAD Viewer.

## Workflow

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. Interaction │───▶│  2. Export      │───▶│  3. Validation  │───▶│  4. Iteration   │
│  Describe intent│    │  Download ZIP   │    │  Run in VS Code │    │  Refine params  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

1. **Interaction**: Describe the mechanical intent. SemiShape generates or refactors the build123d script.
2. **Integration**: Export the code or project structure.
3. **Verification**: Execute locally in VS Code to validate geometry.
4. **Iteration**: Refine parameters or refactor logic based on visual feedback.

## Local Setup

**Prerequisites**: VS Code + [OCP CAD Viewer extension](https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Update pip and install core dependencies (tested with Python 3.13)
pip install --upgrade pip
pip install build123d ocp-vscode

# 3. Execute the generated model
python src/model.py
```

## Project Structure in SemiShape

```text
SemiShape/
├── src/
│   └── model.py      # Generated build123d logic
└── README.md
```

## Best Practices and Standards

SemiShape promotes clean "CAD-as-code" habits:

### 1. Parametrization

```python
# Recommended
WIDTH, HEIGHT = 100.0, 50.0
# Avoid
Box(100.0, 50.0, 10.0)
```

### 2. Modern Syntax (Builder Mode)

```python
# Recommended
with BuildPart() as model:
    Box(WIDTH, HEIGHT, 10)
```

### 3. Robust Selection

```python
# Recommended (Geometric / Using Select.LAST)
top_face = model.faces().sort_by(Axis.Z).last
fillet(model.edges(Select.LAST), radius=2.0)

# Avoid (Index-based)
top_face = model.faces()[0]
```

## Legal and Attribution

Copyright © 2026 Pavel Mareš (painter99)  
This project is open-source under the **Apache License 2.0**.

### Attribution

SemiShape is powered by **build123d: A Python-based parametric CAD library**.  
Core development by **Roger Maitland** and contributors.

If you use this tool in a professional or research context, please recognize the underlying framework:

> Maitland, R. (2025). _build123d: A Python-based parametric CAD library_ (v0.10.0).
> DOI: [10.5281/zenodo.17537673](https://doi.org/10.5281/zenodo.17537673)

### Disclaimer

SemiShape is an **unofficial community tool**. It is **not affiliated with, sponsored by, or endorsed by** the build123d core team.

**Warning**: AI-generated CAD code requires manual review. Always verify geometry and engineering constraints before manufacturing.

---

## Links

- build123d Documentation: <https://build123d.readthedocs.io/>
- Source Framework: <https://github.com/gumyr/build123d>
