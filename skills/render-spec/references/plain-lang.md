# .plain Language Reference

.plain is a specification language designed for writing software requirements in a clear, structured format. It is used to generate production-ready code from `.plain` spec files using AI. The `.plain` files are the source of truth. They describe what the software should do, how it should be built, and how it should be tested. The generated code is a read-only artifact produced by the renderer.

## .plain File Structure

There are two kinds of `.plain` file. A **spec plain file** describes a module. A **test plain file** holds the test scenarios of one functionality of that module.

A spec plain file has a YAML frontmatter section followed by standardized sections (marked with `***section name***` headers):
- `***definitions***` — declares concepts used throughout the specification
- `***implementation reqs***` — non-functional requirements about how the software should be built
- `***test reqs***` — requirements for conformance testing
- `***functional specs***` — describes what the software should do

A test plain file has its own frontmatter and two sections, `***conformance tests***` and `***acceptance tests***`. See *Test Plain Files* below.

Every section marker is at the start of its line. An indented `***...***` line is not a section.

## Concept Notation

Concepts are the building blocks of .plain specifications. They are written between colons: `:ConceptName:`. Valid characters include letters, digits, plus, minus, dot, and underscore.

Concepts must be defined in `***definitions***` before being referenced in other sections. Concept names must be globally unique across the specification and its imports. Concept references must not form cycles — if concept A references concept B, then concept B must not reference concept A.

### Predefined Concepts

.plain provides predefined concepts available in all specifications without needing to be defined:

| Concept | Meaning |
|---------|---------|
| `:plainDefinitions:` | Content of the `***definitions***` section |
| `:plainImplementationReqs:` | Content of the `***implementation reqs***` section |
| `:plainFunctionality:` | Content of the `***functional specs***` section |
| `:plainTestReqs:` | Content of the `***test reqs***` section |
| `:Implementation:` | The system implementing `:plainFunctionality:` |
| `:plainImplementationCode:` | The generated implementation code |
| `:UnitTests:` | Auto-generated unit tests for individual functionalities (configured in `***implementation reqs***`) |
| `:ConformanceTests:` | Tests generated from the `***conformance tests***` scenarios of a functionality |
| `:AcceptanceTest:` / `:AcceptanceTests:` | Tests generated from the `***acceptance tests***` scenarios of a functionality |

## Definitions Section (`***definitions***`)

Declares concepts used throughout the specification. A concept's definition can come from the module's own `***definitions***` section, from an `import`ed module's definitions, or from a `require`d module's `exported_concepts` (but not transitively). Attributes, constraints and clarifications can be nested as sub-bullets (see the example above).

## Implementation Reqs Section (`***implementation reqs***`)

A free-form section for any instructions that steer code generation. Common uses include technology choices, architectural constraints, coding standards, and naming conventions, but it can also contain detailed implementation guidance — data formats, error handling strategies, algorithm descriptions, or any other context the renderer needs to produce correct code. These describe HOW to build the software, not WHAT it should do. Unit-testing specs also go here, not in `***test reqs***`.

## Test Reqs Section (`***test reqs***`)

Specifies requirements for conformance testing — test frameworks, execution methods, and testing constraints. It says HOW `:ConformanceTests:` and `:AcceptanceTests:` are built and run; the scenarios in the test plain files say WHAT they check. It does not refer to unit tests, which are specified in the `***implementation reqs***` section.

## Functional Specs Section (`***functional specs***`)

Describes what the software should do. Each functionality is a `# <func-id>` heading followed by its body — free text that describes the behavior as prose, `- ` bullets, or any other shape. No body line starts with `# ` (that starts the next functionality) or with `***`.

```plain
***functional specs***

# add-task
A :User: can add a :Task:. Only valid :Task: items are added.

# delete-task
A :User: can delete a :Task:.
```

A func-id is lowercase letters, digits and hyphens (`add-task`, `export-csv-2`, `ctrl-d-exit`) and is unique within its module. It is an identity, not a label: a functionality keeps its func-id for as long as it exists, even when its text changes. The func-id names the functionality everywhere — in its test plain files, in the render plan, in logs, and in the names of the generated tests.

Each functional spec must be limited in complexity. If a spec is too complex, the renderer responds with "Functional spec too complex!" and it must be broken down into smaller specs. Complexity is measured in lines of code - each spec should imply no more than 200 lines of code.

Functional specs are in **sequential order** and rendered incrementally, one by one. When a spec is rendered, only **previous** functional specs are in the renderer's context — those earlier in the list, plus any from `requires` modules; later specs are invisible, so a spec can never reference or anticipate what comes after it. The order of the headings is the render order; the func-id itself carries no order. This ordering matters for incremental rendering and for detecting conflicts between specs.

## Test Plain Files

The test scenarios of a functionality live in a test plain file of its own. A spec plain file never holds a `***acceptance tests***` section, nested under a functional spec or at the top level.

```plain
---
module: task-manager
func_id: add-task
---

***conformance tests***

# add-first-task
A :User: adds a :Task: named "Buy milk" to an empty :TaskList:. :TaskList: then shows one :Task: named "Buy milk".

***acceptance tests***

# add-without-name
A :User: adds a :Task: with an empty name. :App: rejects it and :TaskList: stays empty.
```

- The frontmatter has exactly two keys, both required: `module:` is the spec plain file's name without `.plain`, and `func_id:` is the func-id of the functionality the scenarios belong to.
- Both sections are required and `***conformance tests***` comes first. Both may be empty — the minimal valid file is the frontmatter and the two markers.
- `***conformance tests***` holds the scenarios of the **expected use** of the functionality: its main path, with valid parameters, the expected caller, and the data present. They gate the functionality: it is done only when every conformance scenario passes.
- `***acceptance tests***` holds the scenarios of use that is **not expected**: invalid parameters, wrong or missing authentication, missing data. An acceptance scenario is rendered after the conformance tests of its functionality pass.
- A scenario is a `# <scenario-id>` heading followed by free text that says what is done and what result is expected. A scenario-id has the same syntax as a func-id and is unique for its functionality.
- Scenarios describe behavior through the observable interface (CLI, HTTP, files, UI). They never name a function, class or file of the implementation, and the generated test never reaches into the implementation's internals.

By convention a test plain file lives at `tests/<module>/<func-id>.plain`, with `tests/` next to the spec plain file. The location is convention only: a test plain file is bound to its functionality by its frontmatter, not by its path. More than one file may bind to the same functionality, and their scenarios are merged.

The scenarios in these files are the complete and only list of tests for the module. The renderer implements them and nothing else — it never invents a scenario, and it never extends one.

## YAML Frontmatter

The frontmatter is enclosed between `---` markers and supports:

- **`import`** — includes definitions, implementation reqs, and test reqs from templates. Imported modules must not contain functional specs. The default import directory is `template/` — the `template/` prefix is not needed (e.g., `airplain` resolves to `template/airplain.plain`).
- **`requires`** — specifies dependencies on other root-level modules that must be built first. Unlike `import`, required modules can contain functional specs and represent complete software modules. Requires paths point to root-level modules (e.g., `auth`, `messaging`).
- **`description`** — optional description of the specification.
- **`required_concepts`** — concepts that must be defined by any module that imports this spec.
- **`exported_concepts`** — concepts made available to modules that `require` this one. **Exports are not transitive.** A concept exported from module `A` is visible only to modules that `requires: A` directly. If `B` `requires: A` and `C` `requires: B`, the concepts `A` exports are not visible to `C` — only the concepts `B` itself lists in its own `exported_concepts` (re-declaring and forwarding them in its own `***definitions***` as needed).

## Comments

Lines starting with `>` are ignored when rendering:
