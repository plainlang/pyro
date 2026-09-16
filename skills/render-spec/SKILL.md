---
name: render-spec
description: >-
  Renders a .plain specification module into working, tested code. Use when
  asked to render, build, or implement a .plain spec file or module: resolves
  and renders its required/imported modules in dependency order, producing
  implementation code in plain_module/code/, conformance tests in
  plain_module/tests/, and the target module's output in dist/.
metadata:
  version: "0.4.0"
---

# Skill instructions

When starting each step or substep, report with a message "Starting Step <Step_ID>: <Description>".

Do every step yourself. Never hand any step to a subagent, Agent/Task tool or workflow. Module count or spec size are not exceptions.

# Step 0: Python interpreter and version check

`<skill_folder>` is the absolute path of the directory holding this `SKILL.md`. Resolve it now and reuse it everywhere in this skill where `<skill_folder>` is used:
  * On Claude Code it is `${CLAUDE_SKILL_DIR}`; on other agents derive it from the location this skill was loaded from.
  * Never reach a file inside this skill by a relative path.

`<python>` is required Python 3.8 or newer. Resolve it now and reuse it everywhere in this skill where `<python>` is used. Try these candidates one at a time, in this order, and stop at the first one whose output contains a `current:` line - its interpreter is `<python>`. Do not run the remaining candidates once one has succeeded, and do not run them in parallel:
1. `python3 "<skill_folder>/scripts/check_version.py" check`
2. `py -3 "<skill_folder>/scripts/check_version.py" check`
3. `python "<skill_folder>/scripts/check_version.py" check`

Report the Python tool you settled on. If none of the three prints a `current:` line, Python is a missing dependency: abort the rendering and report it.

From that same command's output report with a message "Running pyro: <current>".
* If the output shows `status: update-available`, warn with a message: "A newer pyro release <latest> is available (this is <current>)".
* On any other status, say nothing about updates and continue.

# Step 1: Introduction, inputs and outputs

Your mission is to implement software code as defined by .plain specifications (specs).
To understand the specs language, load the complete `<skill_folder>/references/plain-lang.md`.

Input arguments are:
* <TargetModule> which is the filename of to the module spec to be rendered.

Inputs artifacts are:
* specs of <TargetModule> and the modules it requires or imports, including referenced files inside the specs.

Generated artifacts are:
* :RenderPlan: is a table listing all the modules for rendering and current render state. :RenderPlan: lives in `./.pyro/render-plan.md`.
* :plainImplementationCode: lives under `./plain_module/code`. Every module is rendered into this same folder, each building on top of the previously rendered ones.
* :ConformanceTests: are living under `./plain_module/tests`.
* Internal working files (dependencies, per-module scenarios and requirements) live under `./.pyro`.

### Available tools and paths

`<python>` is the interpreter resolved in Step 0 - always run them with it, and never through a shell of your own, so the same command line works on macOS, Linux and Windows alike.

`scripts/plain_sections.py` extracts one section out of any number of specs and prints it to stdout:
  `<python> "<skill_folder>/scripts/plain_sections.py" [--include-filename] [--output <path>] <section> <spec.plain> [<spec.plain> ...]`
  * `<section>` is one of `defs`, `impl-reqs`, `test-reqs`, `func-specs`, `acc-tests`, `all`.
  * `--output <path>` writes the result to `<path>`.
  * Always gather sections with this script - never transcribe or summarize them by hand.

# Step 2: Prepare the :RenderPlan:

Find and read the frontmatter of <TargetModule> and all specs that <TargetModule> requires.

Ensure there are no loops in the dependency graph of modules. If there are, abandon the work and describe the error (loop).

Prepare the optimal order for rendering <TargetModule> and all the required modules based on the dependency graph.

Prepare a :RenderPlan: : List all the modules to be rendered in the planned rendering order in the example format from `<skill_folder>/references/render-plan.md` and write it to :RenderPlan: file (overwrite if already exists).


## Step 3: Verifying the environment

If any dependency is missing - DO NOT INSTALL ANYTHING, but do:
* immediatly abort the rendering
* report with message listing missing dependencies.

### Step 3.1: Dependencies

Report with a message "Step 3.1: Dependencies".

Gather all :plainImplementationReqs: and :plainTestReqs: from all specs of the modules' to be rendered:
* `<python> "<skill_folder>/scripts/plain_sections.py" --include-filename impl-reqs <all specs to be rendered>`
* `<python> "<skill_folder>/scripts/plain_sections.py" --include-filename test-reqs <all specs to be rendered>`

Write a list of all the required dependencies for implementation and for tests into `.pyro/dependencies.md` file. Verify all the all the dependendencies are present and update the list.

Report with a message showing the `.pyro/dependencies.md`.


## Step 4: Rendering

Render every module yourself - never delegate any module to a subagent, Agent/Task tool or workflow.

Before rendering the first module, create the folders `plain_module/code`, `plain_module/tests` and `.pyro` (skip any that already exist).

Load the :RenderPlan: and for every module follow precisely the steps:

### Step 4.1: Specs, reqs, test scenarios
Report with a message "Step 4.1: Loading specs, writing reqs and test scenarios for: <module> + <required-or-imported-modules>".

Run the command with helper script, where <specs> are the module's spec followed by the specs of its imported or required modules:
`<python> "<skill_folder>/scripts/plain_sections.py" all <specs>`
The output of this command are all the necessary specs for succesfully rendering this module.

Write exhaustive conformance test scenarios for every :plainFunctionality: of the <module>'s spec into `.pyro/<module>/scenarios.md`.
* Scenarios should exhaustively test every :plainFunctionality: and should include :AcceptanceTests:.
* Get the <module>'s :AcceptanceTests: with `<python> "<skill_folder>/scripts/plain_sections.py" acc-tests <module spec>` and cover every one of them.

Write the lists of requirements using the helper script, where <specs> are module's spec plus the specs of its imported modules:
* impl. reqs: `<python> "<skill_folder>/scripts/plain_sections.py" impl-reqs <specs> --output .pyro/<module>/impl-reqs.md`
* test reqs: `<python> "<skill_folder>/scripts/plain_sections.py" test-reqs <specs> --output .pyro/<module>/test-reqs.md`
Both lists hold the requirements verbatim - never paraphrase, reorder or drop any of them.
  
### Step 4.2: Implement code and tests
Report with a message "Step 4.2: Implementation of <module>".

All the implementation code must be put in the self-contained `plain_module/code` folder. Nothing outside of `plain_module` and `.pyro` folders can be touched during this step.

Implement all :plainFunctionality: of <module> specs while respecting all the requirements written in `.pyro/<module>/impl-reqs.md`.

Implement :UnitTests:.

Implement :ConformanceTests: covering all test scenarios:
* Read all test scenarios from `.pyro/<module>/scenarios.md`.
* Read test requirements in `.pyro/<module>/test-reqs.md`.
* Implement the conformance tests covering all test scenarios and respecting test requirements into the `plain_module/tests` folder.

### Step 4.3: Tests verification
Report with a message "#Step 4.3: Tests verification of <module>".

If any tests are failing, go back to the implementation step (4.2), debug it and fix implementation code:
* Run and verify all :ConformanceTests: are passing.
* Run and verify all :UnitTests: are passing.

### Step 4.4: Reqs verification
Report with a message "Step 4.4: Reqs verification of <module>".

Read the list `.pyro/<module>/impl-reqs.md` and for every item:
* Review if the implementation respects it.
* Add checkbox with checked/unchecked status to the item.

Read the list `.pyro/<module>/test-reqs.md` and for every item:
* Review if the conformance tests respect it.
* Add checkbox with checked/unchecked status to the item.

IMPORTANT: if any requirement list item is not passing, go back to the implementation (step 4.2), debug and fix it in the code.


When all 4.x steps are done, continue with rendering the next module until no more modules are left.

## Step 5: Finalize and report

When all modules are rendered do:
- remove installed dependency artifacts (e.g. `node_modules/`, `.venv/`, `__pycache__/`, vendored packages) in `plain_module/code`, but keep the dependency manifests and lock files so dependencies can be reinstalled later.
- copy all of the files in the `plain_module/code` folder to the `./dist` folder:
  `<python> "<skill_folder>/scripts/copy_folder.py" plain_module/code dist`
- prepare a short report on the :plainImplementationCode: and :ConformanceTests:
- present commands to run tests (unit and/or conformance tests)
- present the command to run the rendered <TargetModule>

Finally, report with a message: "pyro <current> (latest: <latest>)" - reiterating pyro versions and update warning resolved in Step 0.