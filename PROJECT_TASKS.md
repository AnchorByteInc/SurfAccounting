# Comprehensive Project Plan: Surf - Feature-Complete Bookkeeping & Invoicing Web Application

⸻

Phase 1 – Project Initialization

1.1 Repository & Folder Structure
[x] 1.1.1 Create project root directory
[x] 1.1.2 Create required folders: frontend/, backend/, tests/, migrations/
[x] 1.1.3 Create empty SQLite file data.sqlite in project root
[x] 1.1.4 Initialize Git repository
[x] 1.1.5 Create .gitignore for Python, Node, SQLite

⸻

1.2 Backend Environment Setup (backend/)
[x] 1.2.1 Create Python virtual environment
[x] 1.2.2 Install dependencies: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Marshmallow, pytest
[x] 1.2.3 Create backend/app.py
[x] 1.2.4 Create backend/config.py with SQLite configuration
[x] 1.2.5 Initialize Flask app factory pattern
[x] 1.2.6 Initialize SQLAlchemy instance
[x] 1.2.7 Initialize Flask-Migrate
[x] 1.2.8 Configure CORS
[x] 1.2.9 Register blueprint structure (auth, customers, vendors, etc.)
[x] 1.2.10 Verify server runs successfully

⸻

1.3 Frontend Setup (frontend/)
[x] 1.3.1 Initialize Vue 3 project using Vite
[x] 1.3.2 Install dependencies: Vue Router, Pinia, Axios, TailwindCSS
[x] 1.3.3 Configure TailwindCSS
[x] 1.3.4 Configure Axios base URL
[x] 1.3.5 Setup folder structure (components/, views/, stores/, router/, services/)
[x] 1.3.6 Create base layout with navigation sidebar
[x] 1.3.7 Confirm frontend dev server runs

⸻

Phase 2 – Core Backend Architecture

2.1 Database Base Models
[x] 2.1.1 Create BaseModel mixin with id, created_at, updated_at
[x] 2.1.2 Add automatic timestamp updating
[x] 2.1.3 Create reusable serialization method

⸻

2.2 Core Accounting Models (backend/models/)

Chart of Accounts
[x] 2.2.1 Create Account model (name, code, type, subtype, parent_id, is_active)
[x] 2.2.2 Enforce unique account code
[x] 2.2.3 Add relationship for parent/child accounts

Customers
[x] 2.2.4 Create Customer model (name, email, phone, billing_address, balance)
[x] 2.2.5 Add validation constraints

Vendors
[x] 2.2.6 Create Vendor model (name, email, phone, address, balance)

Invoices
[x] 2.2.7 Create Invoice model (customer_id, invoice_number, issue_date, due_date, status, subtotal, tax, total, balance)
[x] 2.2.8 Create InvoiceLine model (invoice_id, description, quantity, unit_price, account_id, line_total)
[x] 2.2.9 Add relationship and cascade rules

Bills
[x] 2.2.10 Create Bill model (vendor_id, bill_number, issue_date, due_date, status, total, balance)
[x] 2.2.11 Create BillLine model (bill_id, description, quantity, unit_cost, account_id, line_total)

Double-Entry Accounting
[x] 2.2.12 Create JournalEntry model (date, memo, reference)
[x] 2.2.13 Create JournalEntryLine model (journal_entry_id, account_id, debit, credit)
[x] 2.2.14 Enforce debit/credit balance validation method

Transactions
[x] 2.2.15 Create Transaction model (date, description, reference_type, reference_id)
[x] 2.2.16 Create TransactionDetail model (transaction_id, account_id, debit, credit)

Payments
[x] 2.2.17 Create Payment model (date, amount, customer_id, invoice_id, method)
[x] 2.2.18 Create VendorPayment model (date, amount, vendor_id, bill_id, method)

Bank Accounts
[x] 2.2.19 Create BankAccount model (name, account_number, account_id)
[x] 2.2.20 Create BankReconciliation model (bank_account_id, start_date, end_date, ending_balance, status)

Settings
[x] 2.2.21 Create Settings model (business_name, address, tax_rate, default_currency)

⸻

2.3 Database Migrations
[x] 2.3.1 Initialize Flask-Migrate
[x] 2.3.2 Generate initial migration
[x] 2.3.3 Apply migration
[x] 2.3.4 Seed default Chart of Accounts
[x] 2.3.5 Seed default system accounts (Cash, A/R, A/P, Revenue, Expenses)

⸻

Phase 3 – Business Logic Layer (backend/services/)

3.1 Double-Entry Enforcement
[x] 3.1.1 Implement function to validate debit == credit
[x] 3.1.2 Prevent journal entry save if unbalanced
[x] 3.1.3 Write unit tests for enforcement

⸻

3.2 Invoice Logic
[x] 3.2.1 Implement invoice subtotal calculation
[x] 3.2.2 Implement tax calculation
[x] 3.2.3 Auto-update invoice totals on line changes
[x] 3.2.4 Generate journal entry for invoice (Debit A/R, Credit Revenue)
[x] 3.2.5 Update customer A/R balance

⸻

3.3 Payment Logic
[x] 3.3.1 Apply payment to invoice
[x] 3.3.2 Update invoice balance
[x] 3.3.3 Generate journal entry (Debit Cash, Credit A/R)
[x] 3.3.4 Handle partial payments

⸻

3.4 Bill Logic
[x] 3.4.1 Calculate bill totals
[x] 3.4.2 Generate journal entry (Debit Expense, Credit A/P)
[x] 3.4.3 Update vendor A/P balance

⸻

3.5 Vendor Payment Logic
[x] 3.5.1 Apply vendor payment
[x] 3.5.2 Generate journal entry (Debit A/P, Credit Cash)
[x] 3.5.3 Handle partial bill payments

⸻

Phase 4 – Authentication

4.1 Backend Auth
[x] 4.1.1 Create hardcoded user credentials
[x] 4.1.2 Implement login route returning JWT
[x] 4.1.3 Protect all API routes with JWT
[x] 4.1.4 Write authentication tests

⸻

4.2 Frontend Auth
[x] 4.2.1 Create login page
[x] 4.2.2 Create Pinia auth store
[x] 4.2.3 Store JWT in localStorage
[x] 4.2.4 Implement Axios interceptor for JWT
[x] 4.2.5 Implement route guards

⸻

Phase 5 – API Implementation

5.1 Customers
[x] 5.1.1 Create CRUD endpoints
[x] 5.1.2 Add input validation
[x] 5.1.3 Add pagination
[x] 5.1.4 Add filtering
[x] 5.1.5 Write API tests

5.2 Vendors
[x] 5.2.1 Create CRUD endpoints
[x] 5.2.2 Add input validation
[x] 5.2.3 Add pagination
[x] 5.2.4 Add filtering
[x] 5.2.5 Write API tests

5.3 Invoices
[x] 5.3.1 Create CRUD endpoints
[x] 5.3.2 Add input validation
[x] 5.3.3 Add pagination
[x] 5.3.4 Add filtering
[x] 5.3.5 Write API tests

5.4 InvoiceLines
[x] 5.4.1 Create CRUD endpoints
[x] 5.4.2 Add input validation
[x] 5.4.3 Add pagination
[x] 5.4.4 Add filtering
[x] 5.4.5 Write API tests

5.5 Bills
[x] 5.5.1 Create CRUD endpoints
[x] 5.5.2 Add input validation
[x] 5.5.3 Add pagination
[x] 5.5.4 Add filtering
[x] 5.5.5 Write API tests

5.6 BillLines
[x] 5.6.1 Create CRUD endpoints
[x] 5.6.2 Add input validation
[x] 5.6.3 Add pagination
[x] 5.6.4 Add filtering
[x] 5.6.5 Write API tests

5.7 Accounts
[x] 5.7.1 Create CRUD endpoints
[x] 5.7.2 Add input validation
[x] 5.7.3 Add pagination
[x] 5.7.4 Add filtering
[x] 5.7.5 Write API tests

5.8 JournalEntries
[x] 5.8.1 Create CRUD endpoints
[x] 5.8.2 Add input validation
[x] 5.8.3 Add pagination
[x] 5.8.4 Add filtering
[x] 5.8.5 Write API tests

5.9 Payments
[x] 5.9.1 Create CRUD endpoints
[x] 5.9.2 Add input validation
[x] 5.9.3 Add pagination
[x] 5.9.4 Add filtering
[x] 5.9.5 Write API tests

5.10 BankAccounts
[x] 5.10.1 Create CRUD endpoints
[x] 5.10.2 Add input validation
[x] 5.10.3 Add pagination
[x] 5.10.4 Add filtering
[x] 5.10.5 Write API tests

5.11 Settings
[x] 5.11.1 Create CRUD endpoints
[x] 5.11.2 Add input validation
[x] 5.11.3 Add pagination
[x] 5.11.4 Add filtering
[x] 5.11.5 Write API tests

⸻

Phase 6 – Frontend Features

6.1 Customers UI
[x] 6.1.1 Create customer list page
[x] 6.1.2 Create customer form page
[x] 6.1.3 Add delete confirmation

⸻

6.2 Vendors UI
[x] 6.2.1 Create vendor list page
[x] 6.2.2 Create vendor form page

⸻

6.3 Invoices UI
[x] 6.3.1 Create invoice list page
[x] 6.3.2 Create invoice creation form
[x] 6.3.3 Add dynamic invoice line editing
[x] 6.3.4 Display auto-calculated totals
[x] 6.3.5 Add payment recording modal
[x] 6.3.6 Generate printable PDF invoice

⸻

6.4 Bills UI
[x] 6.4.1 Create bill list page
[x] 6.4.2 Create bill creation form
[x] 6.4.3 Add vendor payment modal

⸻

6.5 Chart of Accounts UI
[x] 6.5.1 Display account hierarchy
[x] 6.5.2 Create account form
[x] 6.5.3 Prevent deletion of system accounts

⸻

Phase 7 – Reporting Engine

7.1 Backend Financial Reports
[x] 7.1.1 Implement Income Statement calculation
[x] 7.1.2 Implement Profit & Loss calculation
[x] 7.1.3 Implement Balance Sheet calculation
[x] 7.1.4 Implement Statement of Cash Flows
[x] 7.1.5 Implement A/R Aging report
[x] 7.1.6 Implement A/P Aging report
[x] 7.1.7 Create API endpoints for each report
[x] 7.1.8 Write financial accuracy tests

⸻

7.2 Frontend Reports UI
[x] 7.2.1 Create reports dashboard page
[x] 7.2.2 Create Income Statement page
[x] 7.2.3 Create Balance Sheet page
[x] 7.2.4 Create Cash Flow page
[x] 7.2.5 Create A/R Aging page
[x] 7.2.6 Create A/P Aging page
[x] 7.2.7 Add PDF export functionality

⸻

Phase 8 – Dashboard
[x] 8.1.1 Create dashboard API endpoint
[x] 8.1.2 Calculate revenue metric
[x] 8.1.3 Calculate expenses metric
[x] 8.1.4 Calculate net income
[x] 8.1.5 Calculate outstanding A/R
[x] 8.1.6 Calculate outstanding A/P
[x] 8.1.7 Calculate cash balance
[x] 8.1.8 Build dashboard UI cards
[x] 8.1.9 Add charts for monthly revenue and expenses

⸻

Phase 9 – Testing & QA (tests/)

9.1 Backend Tests
[x] 9.1.1 Write model validation tests
[x] 9.1.2 Write service layer tests
[x] 9.1.3 Write API integration tests

⸻

9.2 Financial Logic Tests
[x] 9.2.1 Test double-entry enforcement
[x] 9.2.2 Test invoice posting entries
[x] 9.2.3 Test payment journal entries
[x] 9.2.4 Test balance sheet integrity

⸻

9.3 Frontend Tests
[x] 9.3.1 Test login flow
[x] 9.3.2 Test invoice creation flow
[x] 9.3.3 Test payment workflow

⸻

9.4 End-to-End Tests
[x] 9.4.1 Simulate full invoice lifecycle
[x] 9.4.2 Simulate full bill lifecycle
[x] 9.4.3 Validate financial statements after transactions

⸻

Phase 10 – Bug Fixing & Hardening
[x] 10.1.1 Fix validation edge cases (qty/price > 0, due_date >= issue_date, non-negative journal amounts)
[x] 10.1.2 Add database constraints (CHECK for amounts, UNIQUE invoice/bill numbers)
[x] 10.1.3 Improve error handling responses (Global Flask error handlers)
[x] 10.1.4 Improve frontend form validation (HTML5 min/step/date checks, cross-field rules)
[x] 10.1.5 Prevent negative balances (Scoped to cash/bank account outflows)
[x] 10.1.6 Lock closed accounting periods (Enforce in payments and journal saving)
[x] 10.1.7 Add database indexes for performance (FKs, dates, status)

⸻

Phase 11 – Advanced Financial Workflows
[x] 11.1.1 Add API endpoint for posting invoices (triggering service logic)
[x] 11.1.2 Add API endpoint for posting bills (triggering service logic)
[x] 11.1.3 Integrate apply_payment service into create_payment API
[x] 11.1.4 Integrate apply_vendor_payment service into create_vendor_payment API
[x] 11.1.5 Implement consistent monetary rounding and Decimal policy across all services

⸻

Phase 12 – Advanced UI & Administrative Tools


12.1 Admin Dashboard
[x] 12.1.1 Create GL journal entry UI (list, create, edit, delete)

⸻

12.2 Accounting Period Management
[x] 12.2.1 Create accounting period management UI (list, create, close)

⸻

12.3 Balance Verification
[x] 12.3.1 Create balance verification dashboard (integrity checks)

⸻

12.4 Bulk Import Management
[x] 12.4.1 Create bulk import API endpoints (Accounts, Customers, Vendors, Items, Journals)
[x] 12.4.2 Create reusable frontend BulkImportModal component
[x] 12.4.3 Integrate Bulk Import option in relevant list views

12.5 Administrative Utilities
[x] 12.5.1 Create database reset script (drop all, recreate, seed default data)

⸻

Phase 20 – Final Validation
[ ] 20.1.1 Run full test suite
[ ] 20.1.2 Validate financial reports manually
[ ] 20.1.3 Verify double-entry accuracy across all flows
[ ] 20.1.4 Validate PDF generation
[ ] 20.1.5 Perform UX review
[ ] 20.1.6 Confirm no TODOs remain
[ ] 20.1.7 Confirm 100% core financial logic coverage

⸻

End State

When all tasks are complete:
- Fully functional bookkeeping system
- Accurate double-entry accounting
- Complete invoicing & billing workflow
- Full financial reporting suite
- Authenticated single-business environment
- Fully tested backend & frontend
- No incomplete features
- Production-ready local web application

⸻

⸻

**Notes & Maintenance**
- Maintain 100% test coverage for core financial logic
- Ensure all monetary calculations use Decimal
- Document API error codes and validation rules

⸻

**Future Enhancements**
- Implement Audit Log for tracking all financial transaction changes
- Add User Roles and Permissions (e.g., Accountant vs. Viewer)
- Support Multi-currency transactions with automated exchange rate updates
- Add Budgeting module with variance analysis reports