# Intro

This repo includes:
- cp-render skill to render plain specs with an agent like Claude Code (`/cp-render`)
- cp-render-light skill with less instructions
- cp-render-min skill with minimal instruction and plain reference loaded
- cp-render-min-min skill with minimal instructions without plain reference

## Install

Recommended way of installation is scoped per project with "npx skills" tool:

```bash
cd project
npx skills add git@github.com:Codeplain-ai/cp-skills.git --agent claude-code
```

You can verify the skill is installed via:
```bash
npx skills list
```


# Using the skills

Once the skill is installed, start Claude from your project's working dir and prompt `/cp-render <plain-spec-filename>`.