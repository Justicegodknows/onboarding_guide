# TODO

- [ ] Locate and fix all deprecated Zustand default imports (`import create from 'zustand'` → `import { create } from 'zustand'`).
- [x] Update frontend API base URL logic to use same-origin Next proxy on client (`/api/proxy`) to eliminate browser CORS failures.
- [x] Keep server-side API calls direct to backend URL.
- [x] Verify proxy route supports department chat path forwarding.
- [ ] Run checks:
  - [ ] Search for remaining deprecated Zustand import patterns.
  - [x] Run tests/build sanity check relevant to changed files.
