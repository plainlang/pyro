# .plain Language Reference

.plain is a specification language designed for writing software requirements in a clear, structured format. It is used to generate production-ready code from `.plain` spec files using AI. The `.plain` files are the source of truth. They describe what the software should do, how it should be built, and how it should be tested. The generated code is a read-only artifact produced by the renderer.

## .plain File Structure

A `.plain` file has a YAML frontmatter section followed by standardized sections (marked with `***section name***` headers):
- `***definitions***` — declares concepts used throughout the specification
- `***implementation reqs***` — non-functional requirements about how the software should be built
- `***test reqs***` — requirements for conformance testing
- `***functional specs***` — describes what the software should do

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
| `:ConformanceTests:` | Auto-generated tests that verify implementation conforms to specs |
| `:AcceptanceTest:` / `:AcceptanceTests:` | Tests that validate specific aspects of the implementation |

## Definitions Section (`***definitions***`)

Declares concepts used throughout the specification. A concept's definition can come from the module's own `***definitions***` section, from an `import`ed module's definitions, or from a `require`d module's `exported_concepts` (but not transitively). Attributes, constraints and clarifications can be nested as sub-bullets (see the example above).

## Implementation Reqs Section (`***implementation reqs***`)

A free-form section for any instructions that steer code generation. Common uses include technology choices, architectural constraints, coding standards, and naming conventions, but it can also contain detailed implementation guidance — data formats, error handling strategies, algorithm descriptions, or any other context the renderer needs to produce correct code. These describe HOW to build the software, not WHAT it should do. Unit-testing specs also go here, not in `***test reqs***`.

## Test Reqs Section (`***test reqs***`)

Specifies requirements for conformance testing — test frameworks, execution methods, and testing constraints. It does not refer to unit tests, which are specified in the `***implementation reqs***` section.

## Functional Specs Section (`***functional specs***`)

Describes what the software should do. Each bullet point is a single piece of functionality that will be implemented.

Each functional spec must be limited in complexity. If a spec is too complex, the renderer responds with "Functional spec too complex!" and it must be broken down into smaller specs. Complexity is measured in lines of code - each spec should imply no more than 200 lines of code.

Functional specs are in **sequential order** and rendered incrementally, one by one. When a spec is rendered, only **previous** functional specs are in the renderer's context — those earlier in the list, plus any from `requires` modules; later specs are invisible, so a spec can never reference or anticipate what comes after it. This ordering matters for incremental rendering and for detecting conflicts between specs.

## Acceptance Tests (`***acceptance tests***`)

Nested under individual functional specs to specify how to verify correct implementation. They extend conformance tests.

## YAML Frontmatter

The frontmatter is enclosed between `---` markers and supports:

- **`import`** — includes definitions, implementation reqs, and test reqs from templates. Imported modules must not contain functional specs. The default import directory is `template/` — the `template/` prefix is not needed (e.g., `airplain` resolves to `template/airplain.plain`).
- **`requires`** — specifies dependencies on other root-level modules that must be built first. Unlike `import`, required modules can contain functional specs and represent complete software modules. Requires paths point to root-level modules (e.g., `auth`, `messaging`).
- **`description`** — optional description of the specification.
- **`required_concepts`** — concepts that must be defined by any module that imports this spec.
- **`exported_concepts`** — concepts made available to modules that `require` this one. **Exports are not transitive.** A concept exported from module `A` is visible only to modules that `requires: A` directly. If `B` `requires: A` and `C` `requires: B`, the concepts `A` exports are not visible to `C` — only the concepts `B` itself lists in its own `exported_concepts` (re-declaring and forwarding them in its own `***definitions***` as needed).

## Comments

Lines starting with `>` are ignored when rendering: