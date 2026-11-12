# Kryon Protocol documentation

Source for the Kryon Protocol technical documentation, built with [Docusaurus](https://docusaurus.io/) and served at `/docs` on the web application.

## Develop and build

```bash
cd docs
npm install
npm start          # development server, http://localhost:3000
npm run build      # static site in ./build
npm run serve      # preview the production build
```

`npm run docs:build` in `client/` builds this site and copies it into `client/public/docs`.

## Structure

```text
docs/
├── docusaurus.config.ts     Site configuration
├── sidebars.ts              Built from the folder structure
├── src/, static/            Theme and images
├── docs/                    Pages, served at /docs/
│   ├── index.md             Welcome page
│   ├── 01-overview/         Introduction, glossary
│   ├── 02-architecture/     System, trust boundary, repository, integrations, oracle
│   ├── 03-smart-contracts/  One page per contract, crates, errors, deployments
│   ├── 04-trading-mechanics/ Orders, matching, settlement, positions, margin, funding,
│   │                         collateral, liquidation, insurance, markets
│   ├── 05-infrastructure/   Services, matcher, indexing, database, real-time, frontend, hosting
│   ├── 06-developer-guides/ Local development, configuration, contracts, bots, signing
│   ├── 07-api-reference/    REST, WebSocket, units, contract calls
│   ├── 08-security/         Security model, mechanisms, access control, emergency controls
│   └── 09-operations/       Deployment, governance, monitoring, runbooks
├── diagrams/
│   ├── excalidraw/          Editable sources
│   ├── svg/, png/           Exports
│   ├── fonts/               Virgil, Excalidraw's hand-drawn font (SIL OFL)
│   └── tools/               Generator and validator
└── reports/                 Internal audit and validation reports, not published
```

Folder number prefixes set the order and are dropped from URLs, so `03-smart-contracts/vault.md` is served at `/docs/smart-contracts/vault`.

## Diagrams

Every diagram exists as `.excalidraw`, `.svg` and `.png` with the same name. All text uses Virgil.

```bash
python3 docs/diagrams/tools/build.py          # rebuild all diagrams and check for overlaps
python3 docs/diagrams/tools/build.py oracle   # rebuild matching names only
python3 docs/diagrams/tools/validate.py       # links, images, diagram files, contract functions
```

To edit a diagram by hand, open its `.excalidraw` file in Excalidraw, export SVG and PNG with a white background under the same name, and remove it from the `ALL` list in its `defs_*.py` so the generator does not overwrite your edit.

## Writing style

- Write like a founder explaining the system to a sharp engineer: first person plural, short sentences, no filler.
- Keep pages compact. Lead with the diagram or the table, then add only what the reader needs.
- No em dashes, no emojis, no hype.
- Every function name, parameter, constant and number must match the source code.
- Give units for every number: 10^18 prices, 10^7 sizes, bps.
- Link pages with relative `.md` paths and repository files with full GitHub URLs.
- `npm run build` must finish with no broken links or anchors.
