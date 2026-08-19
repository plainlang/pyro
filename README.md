# Intro

This repo includes `pyro-render` skill to render plain specs with an agent like Claude Code (`/cp-render`).

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

Once the skill is installed, start Claude from your project's working dir and prompt `/pyro-render <plain-spec-filename>`.