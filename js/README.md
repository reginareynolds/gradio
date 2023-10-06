# gradio-ui

This folder contains all of the Gradio UI and component source code.

- [gradio-ui](#gradio-ui)
  - [Set up](#set-up)
  - [Running the application](#running-the-application)
  - [Local development](#local-development)
  - [Building for production](#building-for-production)
  - [Quality checks](#quality-checks)
    - [Formatting](#formatting)
    - [Type checking](#type-checking)
  - [CI checks](#ci-checks)
    - [Static checks](#static-checks)
    - [Functional test](#functional-test)

## Set up

This folder is managed as 'monorepo' a multi-package repository which make dependency management very simple. In order to do this we use `pnpm` as our package manager.

Make sure [`pnpm`](https://pnpm.io/) is installed by [following the installation instructions for your system](https://pnpm.io/installation).

You will also need `node` which you probably already have

## Running the application

Install all dependencies:

```bash
pnpm i
```

This will install the dependencies for all packages and link any local packages

## Local development

To develop locally, open two terminal tabs from the root of the repository.

Run the python test server, from the root directory:

```bash
cd demo/kitchen_sink
python run.py
```

This will start a development server on port `7860` that the web app is expecting.

Run the web app:

```bash
pnpm dev
```

## Building for production

Run the build:

```bash
pnpm build
```

This will create the necessary files in `js/app/public` and also in `gradio/templates/frontend`.

## Quality checks

The repos currently has two quality checks that can be run locally and are run in CI.

### Formatting

Formatting is handled by [`prettier`](https://prettier.io/) to ensure consistent formatting and prevent style-focused conversations. Formatting failures will fails CI and should be reoslve before merging.

To check formatting:

```bash
pnpm format:check
```

If you have formatting failures then you can run the following command to fix them:

```bash
pnpm format:write
```

### Type checking

We use [TypeScript](https://www.typescriptlang.org/) to provide static types to javascript code. These checks are also run in CI.

to typecheck the code:

```bash
pnpm ts:check
```

## CI checks

Currently the following checks are run in CI:

### Static checks

- Format check (`pnpm format:check`)
- Build css (`pnpm css`)
- Build client (`pnpm build`)
- Type check (`pnpm ts:check`)
- Unit tests (`pnpm test:run`)

### Functional test

```
pip install -r demo/outbreak_forecast/requirements.txt
pnpm exec playwright install chromium
pnpm exec playwright install-deps chromium
pnpm test:browser:full
```
