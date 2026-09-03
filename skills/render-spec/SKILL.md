---
name: render-spec
description: >-
  Renders a .plain specification module into working, tested code. Use when
  asked to render, build, or implement a .plain spec file or module: resolves
  and renders its required/imported modules in dependency order, producing
  implementation code in plain_modules/, conformance tests in conf_tests/,
  and the target module's output in dist/.
argument-hint: <TargetModule>
metadata:
  version: "0.1.0"
---

# Skill instructions

Report with "Running pyro/render-spec: <skill-version>".

When starting each step or substep, report with a message "Starting Step <Step_ID>: <Description>".

# Step 1: Introduction, inputs and outputs

Your mission is to implement software code as defined by .plain specifications (specs).
To understand the specs language, load the complete `<skill_folder>/references/plain-lang.md`.

Input arguments are:
* <TargetModule> which is the filename of to the module spec to be rendered.

Inputs artifacts are:
* specs of <TargetModule> and the modules it requires or imports, including referenced files inside the specs.

Generated artifacts are:
* :RenderPlan: is a table listing all the modules for rendering and current render state. :RenderPlan: lives in `./render-plan.md`.
* :plainImplementationCode: lives under  `./plain_modules` and follow `./plain_modules/<module>` folder structure.
* :plainOutputCode: is the :plainImplementationCode: of the <TargetModule>.
* :ConformanceTests: are living under `./conf_tests` and follow `./conf_tests/<module>` folder structure.

### Available tools and paths
`<skill_folder>` is the absolute path of the directory holding this `SKILL.md`. Resolve it once, now, and reuse it for every file inside this skill:
  * On Claude Code it is `${CLAUDE_SKILL_DIR}`; on other agents derive it from the location this skill was loaded from.
  * Never reach a file inside this skill by a relative path.

`<python>` is the interpreter resolved in Step 3.0 - always run them with it, and never through a shell of your own, so the same command line works on macOS, Linux and Windows alike.

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

### Step 3.0: Python interpreter
Report with a message "Step 3.0: Python interpreter".

The tooling needs Python 3.8 or newer. Resolve it now before any other command, and reuse it as `<python>` everywhere below.

Try these in order, keep the first that prints `ok`:
* `py -3 "<skill_folder>/scripts/plain_sections.py" --check`
* `python3 "<skill_folder>/scripts/plain_sections.py" --check`
* `python "<skill_folder>/scripts/plain_sections.py" --check`

Report the one you settled on. If none prints `ok`, Python is a missing dependency: abort the rendering.

### Step 3.1: Dependencies

Report with a message "Step 3.1: Dependencies".

Gather all :plainImplementationReqs: and :plainTestReqs: from all specs of the modules' to be rendered:
* `<python> "<skill_folder>/scripts/plain_sections.py" --include-filename impl-reqs <all specs to be rendered>`
* `<python> "<skill_folder>/scripts/plain_sections.py" --include-filename test-reqs <all specs to be rendered>`

Write a list of all the required dependencies for implementation and for tests into `dependencies.md` file. Verify all the all the dependendencies are present and update the list.

Report with a message showing the `dependencies.md`.


## Step 4: Rendering

Load the :RenderPlan: and for every module follow precisely the steps:

### Step 4.0: Folder preparation
Report with a message "Step 4.0: Folder preparation of <module>".

Create module's conformance tests folder `conf_tests/<module>`.

Create module's implementation code folder `plain_modules/<module>`.

If there's previous rendered module: copy complete contents of `plain_modules/<previous-module>` folder to the current module's folder `plain_modules/<module>` (e.g. on unix with a command: `cp -r plain_modules/<previous_module>/* plain_modules/<module>/`).

### Step 4.1: Specs, reqs, test scenarios
Report with a message "Step 4.1: Loading specs, writing reqs and test scenarios for: <module> + <required-or-imported-modules>".

Run the command with helper script, where <specs> are the module's spec followed by the specs of its imported or required modules:
`<python> "<skill_folder>/scripts/plain_sections.py" all <specs>`
The output of this command are all the necessary specs for succesfully rendering this module.

Write exhaustive conformance test scenarios for every :plainFunctionality: of the <module>'s spec into `conf_tests/<module>/scenarios.md`.
* Scenarios should exhaustively test every :plainFunctionality: and should include :AcceptanceTests:.
* Get the <module>'s :AcceptanceTests: with `<python> "<skill_folder>/scripts/plain_sections.py" acc-tests <module spec>` and cover every one of them.

Write the lists of requirements using the helper script, where <specs> are module's spec plus the specs of its imported modules:
* impl. reqs: `<python> "<skill_folder>/scripts/plain_sections.py" impl-reqs <specs> --output plain_modules/<module>/impl-reqs.md`
* test reqs: `<python> "<skill_folder>/scripts/plain_sections.py" test-reqs <specs> --output plain_modules/<module>/test-reqs.md`
Both lists hold the requirements verbatim - never paraphrase, reorder or drop any of them.
  
### Step 4.2: Implement code and tests
Report with a message "Step 4.2: Implementation of <module>".

All the implementation code must be put in a self-contained `plain_modules/<module>` folder. NOTHING OUTSIDE OF THIS FOLDER can be touched during this step 4.2.

When referencing already rendered modules, ALWAYS REFER TO THEM RELATIVE FROM `plain_modules/<module>` folder - never include `plain_modules/<module>` in the import or require path.

Implement all :plainFunctionality: of <module> specs while respecting all the requirements in `plain_modules/<module>/impl-reqs.md`.

Implement :UnitTests:.

Implement :ConformanceTests: covering all test scenarios:
* Read all test scenarios from `conf_tests/<module>/scenarios.md`.
* Read test requirements in `plain_modules/<module>/test-reqs.md`.
* Implement the conformance tests covering all test scenarios and respecting test requirements into the `conf_tests/<module>` folder.

### Step 4.3: Tests verification
Report with a message "#Step 4.3: Tests verification of <module>".

If any tests are failing, go back to the implementation step (4.2), debug it and fix implementation code:
* Run and verify <module>'s :ConformanceTests: are passing.
* Run and verify <module>'s :UnitTests: are passing.

### Step 4.4: Reqs verification
Report with a message "Step 4.4: Reqs verification of <module>".

Read the list `plain_modules/<module>/impl-reqs.md` and for every item:
* Review if the implementation respects it.
* Add checkbox with checked/unchecked status to the item.

Read the list `plain_modules/<module>/test-reqs.md` and for every item:
* Review if the conformance tests respect it.
* Add checkbox with checked/unchecked status to the item.

IMPORTANT: if any requirement list item is not passing, go back to the implementation (step 4.2), debug and fix it in the code.

### Step 4.5: Module folder cleanup
Report with a message "Step 4.5: Module folder cleanup".

Remove any temporary files inside `plain_modules/<module>` folder:
* `test-reqs.md` and `impl-reqs.md`.
* any files that are result of testing or debugging during rendering.


When all 4.x steps are done, continue with rendering the next module until no more modules are left.

## Step 5: Finalize and report

When all modules are rendered do:
- copy all of the files in the `plain_modules/<TargetModule>` folder to the `./dist` folder
- prepare a short report on the :plainImplementationCode: and :ConformanceTests:
- present commands to run tests (unit and/or conformance tests)
- present the command to run the rendered <TargetModule>