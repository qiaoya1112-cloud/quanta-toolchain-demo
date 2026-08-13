# React and Ant Design Integration Design

## Objective

Add a reusable React prototype workspace to the existing Flask repository without rewriting or destabilizing current Jinja pages. The first React page will be the internal AI-assisted product workflow showcase, available at `/workflow`.

The integration must also establish a path for future prototypes to use real Ant Design components while existing Flask pages continue to work unchanged.

## Scope

### In Scope

- Add a Vite, React, and Ant Design frontend under `frontend/`.
- Add the first page at `/workflow`.
- Build frontend assets into a Flask-served static directory.
- Reuse the Quanta primary color `#149DAA` through Ant Design theme tokens.
- Implement the agreed workflow showcase structure:
  - 30-second overview.
  - Eight-stage workflow navigation.
  - Stage details for inputs, methods, outputs, responsibilities, completion criteria, and common mistakes.
  - Previous and next stage navigation.
  - Empty Quanta case-study placeholder.
- Preserve the current Flask application, routes, mock data, and deployment entry point.
- Document local development and production build commands.

### Out of Scope

- Rewriting existing Flask and Jinja pages in React.
- Migrating existing inline CSS or JavaScript.
- Adding a database, authentication, CMS, or new backend APIs.
- Implementing real Quanta case-study content.
- Introducing a second component library such as shadcn/ui or Element Plus.
- Sharing runtime state between existing Jinja pages and the workflow showcase.

## Architecture

```text
Browser
├── Existing URLs
│   └── Flask + Jinja + existing inline CSS and JavaScript
└── /workflow
    └── Flask serves the React entry document
        └── Vite-built React + Ant Design assets

Repository
├── toolchain_demo.py
├── static/
│   └── workflow/              # Generated Vite build output
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── content/
        │   └── workflow.js
        ├── components/
        │   ├── WorkflowOverview.jsx
        │   ├── StageDetail.jsx
        │   └── CasePlaceholder.jsx
        └── styles/
            └── app.css
```

Flask remains the application host. React is an isolated frontend island with its own source tree and build process. The generated frontend files are served through Flask's existing static route.

## Routing and Asset Strategy

- Add a Flask route at `/workflow`.
- The route serves `static/workflow/index.html` after a successful frontend build.
- If the build output is missing, return a clear development message with the required build command instead of a server error.
- Vite uses `/` as its base path during development.
- Vite uses `/static/workflow/` as its base path during production builds.
- The first version does not use React Router because it contains a single frontend page and stage navigation is local UI state.

## Development Workflow

During frontend development:

```bash
cd frontend
npm install
npm run dev
```

The workflow page is previewed through the Vite development server for hot reload.

To verify Flask integration:

```bash
cd frontend
npm run build
cd ..
python toolchain_demo.py
```

The integrated page is then available at `http://localhost:5004/workflow`.

## UI and Component Strategy

Ant Design provides interaction primitives and consistent states. Custom layout CSS provides the editorial presentation required by an internal methodology page.

Use Ant Design for:

- Buttons.
- Tags.
- Tabs or segmented navigation where appropriate.
- Collapse panels.
- Progress feedback.
- Tooltips.
- Empty states.
- Copy confirmation messages.

Use custom React layout components for:

- Hero content.
- Eight-stage workflow strip.
- Human and AI responsibility comparison.
- Stage reading layout.
- Case-study placeholder.

The page must use a single light theme with `#149DAA` as the primary accent. It must avoid decorative gradients, excessive cards, large rounded corners, and marketing-style filler copy.

## Content Model

Workflow content is separate from page components. Every stage follows one schema:

```js
{
  id,
  number,
  title,
  summary,
  required,
  purpose,
  inputs,
  steps,
  aiResponsibilities,
  pmResponsibilities,
  outputs,
  completionCriteria,
  commonMistakes,
  promptTemplate
}
```

This lets future requirement iterations change workflow content without restructuring React components.

## Initial User Experience

1. The user lands on a self-explanatory overview with the purpose and expected reading time.
2. The full eight-stage workflow is visible without requiring prior explanation.
3. The user selects a stage to view its execution guide.
4. The guide shows the stage goal, required inputs, standard method, human and AI responsibilities, outputs, completion criteria, and common mistakes.
5. The user can continue with previous and next stage controls.
6. The Quanta case-study area remains visibly marked as planned content.

The workflow is presented as a customizable playbook with mandatory quality gates. Simple work may combine optional stages, but requirement understanding, business confirmation, and solution validation cannot be skipped.

## Error and Empty States

- Missing frontend build: Flask returns a readable setup page with `npm install` and `npm run build` instructions.
- Missing prompt template: the copy action is not rendered.
- Missing case study: render the approved placeholder rather than fabricated content.
- Invalid stage selection: fall back to the first stage.
- Clipboard failure: show a non-blocking failure message and leave the template visible for manual copying.

## Deployment

The Flask start command remains unchanged. The deployment build must install frontend dependencies and run the Vite build before starting Gunicorn.

The intended build sequence is:

```bash
pip install -r requirements.txt
cd frontend
npm ci
npm run build
```

Deployment configuration changes will be limited to the build command. The React output remains static and requires no Node.js process at runtime.

## Verification

- `npm run build` completes without warnings that affect operation.
- The generated `static/workflow/index.html` references `/static/workflow/` assets.
- Flask starts successfully with the existing command.
- `/workflow` returns the React page after a build.
- Existing representative routes such as `/`, `/data`, and `/model` still return successfully.
- Stage selection, previous and next navigation, collapse panels, and prompt copying work.
- The page remains usable at desktop presentation width and mobile width.
- Browser console contains no runtime errors.

## Iteration Boundary

Future new prototypes should be added as React pages when they need real component-library behavior. Existing Flask pages remain in Jinja until a specific redesign justifies migrating that page. A new prototype does not require a repository-wide migration.
