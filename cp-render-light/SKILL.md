---
name: cp-render-light
description: >-
  Renders .plain specs into working software by generating production code.
argument-hint: <TargetModule>
---

# Skill instructions

When starting each step or substep, report with a message "Starting Step <Step_ID>: <Description>".

# Step 1: Introduction, inputs and outputs

Your mission is to implement software code as defined by .plain specifications (specs).
To understand the specs language, load the complete `references/plain-lang.md`.

Input arguments are:
* <TargetModule> which is the filename of to the module spec to be rendered.

Inputs artifacts are:
* specs of <TargetModule> and the modules it requires or imports, including referenced files inside the specs.

Generated artifacts are:
* :RenderPlan: is a table listing all the modules for rendering and current render state. :RenderPlan: lives in `./render-plan.md`.
* :plainImplementationCode: lives under  `./plain_modules` and follow `./plain_modules/<module>` folder structure.
* :plainOutputCode: is the :plainImplementationCode: of the <TargetModule>.
* :ConformanceTests: are living under `./conf_tests` and follow `./conf_tests/<module>` folder structure.

Available tooling:
* `scripts/plain-sections.sh` extracts one section out of any number of specs and prints it to stdout:
  `sh <skill_folder>/scripts/plain-sections.sh [--include-filename] <section> <spec.plain> [<spec.plain> ...]`
  * `<section>` is one of `defs`, `impl-reqs`, `test-reqs`, `func-specs`, `acc-tests`.
  * Exit code 1 means a spec could not be read and 2 means the invocation was wrong - in both cases fix the call instead of falling back to reading the sections yourself. A section missing from a spec is only a warning on stderr.
  * Always gather sections with this script - never transcribe or summarize them by hand.

# Step 2: Prepare the :RenderPlan:

Find and read the frontmatter of <TargetModule> and all specs that <TargetModule> requires.

Ensure there are no loops in the dependency graph of modules. If there are, abandon the work and describe the error (loop).

Prepare the optimal order for rendering <TargetModule> and all the required modules based on the dependency graph.

Prepare a :RenderPlan: : List all the modules to be rendered in the planned rendering order in the [example format](references/render-plan.md) and write it to :RenderPlan: file (overwrite if already exists).


## Step 3: Verifying the environment

If any dependency is missing - DO NOT INSTALL ANYTHING, but do:
* immediatly abort the rendering
* report with message listing missing dependencies.

Gather all :plainImplementationReqs: and :plainTestReqs: from all specs of the modules' to be rendered:
* `sh <skill_folder>/scripts/plain-sections.sh --include-filename impl-reqs <all specs to be rendered>`
* `sh <skill_folder>/scripts/plain-sections.sh --include-filename test-reqs <all specs to be rendered>`

Write a list of all the required dependencies for implementation and for tests into `dependencies.md` file. Verify all the all the dependendencies are present and update the list.

Report with a message showing the `dependencies.md`.


## Step 4: Rendering

Load the :RenderPlan: and for every module follow precisely the steps:

### Step 4.1: Specs, test scenarios and requirements
Report with a message "Step 4.1: Loading specs and writing test scenarios for: <module> + <required-or-imported-modules>".

Read all the specs for this <module> and its required and imported specs.

Write exhaustive conformance test scenarios for every :plainFunctionality: of the <module>'s spec into `conf_tests/<module>/scenarios.md`.
* Scenarios should exhaustively test every :plainFunctionality: and should include :AcceptanceTests:.
* Get the <module>'s :AcceptanceTests: with `sh <skill_folder>/scripts/plain-sections.sh acc-tests <module spec>` and cover every one of them.

Write the lists of requirements with the helper script, where <specs> is the <module>'s spec followed by the specs of its imported modules:
* `sh <skill_folder>/scripts/plain-sections.sh impl-reqs <specs> > plain_modules/<module>/impl-reqs.md`
* `sh <skill_folder>/scripts/plain-sections.sh test-reqs <specs> > plain_modules/<module>/test-reqs.md`

Both lists hold the requirements verbatim - never paraphrase, reorder or drop any of them (Step 4.4 later annotates these same lists with the verification results).

  
### Step 4.2: Implement code and tests
Report with a message "Step 4.2: Implementation of <module>".

All the implementation code must be put in a self-contained `plain_modules/<module>` folder. NOTHING OUTSIDE OF THIS FOLDER can be touched during this step 4.2.

When referencing other rendered modules, ALWAYS FIRST COPY OTHER MODULE'S CODE FROM `plain_modules/used_module/*` INTO `plain_modules/<module>` folder. After it is copied, you can make changes to it. When referencing these modules them, ALWAYS REFER TO THEM RELATIVE FROM `plain_modules/<module>` folder - never include `plain_modules` in the path.

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
Report with a message "#Step 4.4: Reqs verification of <module>".

If there are any requirements not fulfiled, go back to the implementation step (4.2), debug it and fix implementation code.
* Check every item in the list `plain_modules/<module>/impl-reqs.md` if the implementation respects it. Update the list with passed/failed signs.
* Check every item in the list `plain_modules/<module>/test-reqs.md` if the conformance tests respects it. Update the list with passed/failed signs.

When all 4.x steps are done, continue with rendering the next module until no more modules are left.

## Step 5: Finalize and report

When all modules are rendered do:
- copy all of the files in the `plain_modules/<TargetModule>` folder to the `./dist` folder
- prepare a short report on the :plainImplementationCode: and :ConformanceTests:
- present commands to run tests (unit and/or conformance tests)
- present the command to run the rendered <TargetModule>