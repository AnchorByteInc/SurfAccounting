# GitHub Readiness Checklist - Surf Accounting

This checklist details the actionable tasks required to prepare the **Surf Accounting** project for public access on GitHub.

---

### 1. Security & Privacy Hardening
- [ ] **Remove Hardcoded Credentials**: Remove `AUTH_USER` and `AUTH_PASS` from `backend/config.py`. These should be handled via a database or environment variables.
- [ ] **Rotate & Secure Secret Keys**: Update `backend/config.py` to ensure `SECRET_KEY` and `JWT_SECRET_KEY` are ONLY loaded from environment variables in production. Log a warning if default development keys are used.
- [ ] **Fix Git Tracking Issues**:
    - [ ] Remove `.env` from Git tracking (currently tracked) using `git rm --cached .env`.
    - [ ] Remove `.idea/` folder from Git tracking.
    - [ ] Update `.gitignore` to explicitly exclude `.env` (currently missing).
- [ ] **Clean Data Artifacts**: 
    - [ ] Delete all `.sqlite` backup files from the root directory.
    - [ ] Ensure `data.sqlite` is NOT tracked (currently ignored, but verify no real data has been committed).
- [ ] **Sanitize Uploads**: Clear the `uploads/` folder of any non-sample files (user-uploaded logos, etc.) before the first public push.
- [ ] **Audit Sensitive Logs**: Ensure no sensitive data (passwords, tokens) is being printed to the console or log files.

### 2. Documentation (Crucial for Public Access)
- [x] **Revamp main `README.md`**:
    - [x] Rename `READ_ME.md` to `README.md` for standard GitHub recognition.
    - [x] Add a clear project description, feature list, and tech stack overview.
    - [x] Add "Getting Started" section with prerequisites (Python 3.13+, Node.js, etc.).
    - [x] Provide step-by-step setup instructions for both Backend and Frontend.
    - [x] Document the MCP server's purpose and how to connect it.
- [x] **Create `.env.example`**: Provide a template file showing all required environment variables without real values.
- [x] **Populate `mcp_server/README.md`**: Currently empty; needs specific setup and usage instructions for the Model Context Protocol server.
- [x] **API Reference**: Add a basic Markdown file or link to auto-generated docs (if applicable) describing the main API endpoints.
- [x] **Contributing Guide**: Add `CONTRIBUTING.md` defining the workflow for bug reports and pull requests.
- [x] **Security Policy**: Add `SECURITY.md` explaining how users should report vulnerabilities.

### 3. Code Quality & Standards
- [ ] **Metadata Consistency**: 
    - [ ] Update `pyproject.toml` with `authors`, `repository`, and `keywords`.
    - [ ] Sync versioning across `pyproject.toml` and `frontend/package.json`.
- [ ] **Linting & Formatting**: 
    - [ ] Run a formatter (e.g., `black` or `ruff`) on the backend.
    - [ ] Run `prettier` on the frontend code.
- [ ] **Remove Debug Artifacts**: Audit for `print()` statements, excessive commented-out code, and resolved `TODO` comments.
- [ ] **Standardize naming**: Ensure consistent naming conventions between backend (Python/SnakeCase) and frontend (JS/CamelCase) API interactions.

### 4. Project Structure & Cleanup
- [x] **Organize Root Directory**: Consider moving utility scripts like `reset_db.py` to a `scripts/` or `tools/` folder.
- [x] **Dependency Audit**: 
    - [x] Ensure all backend dependencies are explicitly listed in `pyproject.toml`.
    - [x] Remove any unused packages from `package.json`.
- [x] **Consistent Branding**: Ensure the name "Surf" or "Surf Accounting" is used consistently across all documentation and UI.

### 5. GitHub Integration & CI/CD
- [x] **GitHub Actions**: Create a `.github/workflows/ci.yml` to automatically run:
    - [x] Backend tests (`pytest`).
    - [x] Frontend tests (`vitest`).
    - [x] Linter checks.
- [x] **Issue Templates**: Add `.github/ISSUE_TEMPLATE/` for Bug Reports and Feature Requests.
- [x] **License Visibility**: Verify that the `license` file is correctly formatted so GitHub displays it on the main repo page. (Renamed to `LICENSE`)

### 6. Final "Fresh Start" Validation
- [ ] **Cold Setup Test**: Clone the repo into a temporary directory and follow the `README.md` instructions from scratch to ensure nothing is missing.
- [ ] **Verify Production Build**: Run `npm run build` on the frontend to ensure no build-time errors exist.
- [ ] **Verify MCP Server**: Ensure the MCP server starts correctly and the `mcp_server/instance.py` logic is decoupled from local paths.
