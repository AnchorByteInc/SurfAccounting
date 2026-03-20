# Surf Accounting API Reference

The Surf Accounting API is a RESTful API built with Flask. All requests and responses use JSON.

## Base URL

The default development base URL is: `http://localhost:5001/api`

## Authentication

Most endpoints require a JWT token in the `Authorization` header:
`Authorization: Bearer <your_token>`

### Auth Endpoints

- `POST /auth/login`: Authenticate a user and receive a JWT token.
- `POST /auth/forgot-password`: Request a password reset link.
- `POST /auth/reset-password`: Reset a password using a token.

## Resources

### Customers

- `GET /customers`: List all customers.
- `POST /customers`: Create a new customer.
- `GET /customers/<id>`: Get details for a specific customer.
- `PUT /customers/<id>`: Update a customer.
- `DELETE /customers/<id>`: Delete a customer.

### Vendors

- `GET /vendors`: List all vendors.
- `POST /vendors`: Create a new vendor.
- `GET /vendors/<id>`: Get details for a specific vendor.
- `PUT /vendors/<id>`: Update a vendor.
- `DELETE /vendors/<id>`: Delete a vendor.

### Invoices

- `GET /invoices`: List all invoices.
- `POST /invoices`: Create a new invoice.
- `GET /invoices/<id>`: Get details for a specific invoice.
- `PUT /invoices/<id>`: Update an invoice.
- `DELETE /invoices/<id>`: Delete an invoice.

### Bills

- `GET /bills`: List all bills.
- `POST /bills`: Create a new bill.
- `GET /bills/<id>`: Get details for a specific bill.
- `PUT /bills/<id>`: Update a bill.
- `DELETE /bills/<id>`: Delete a bill.

### Chart of Accounts

- `GET /accounts`: List all accounts.
- `POST /accounts`: Create a new account.
- `GET /accounts/<id>`: Get account details.

### Payments

- `GET /payments`: List all payments.
- `POST /payments`: Record a new payment.

### Reports

- `GET /reports/balance-sheet`: Generate a Balance Sheet.
- `GET /reports/profit-loss`: Generate a Profit and Loss statement.

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request successful.
- `201 Created`: Resource created successfully.
- `400 Bad Request`: Validation error or invalid input.
- `401 Unauthorized`: Authentication failed or missing token.
- `404 Not Found`: Resource not found.
- `409 Conflict`: Database integrity error (e.g., duplicate entry).
- `500 Internal Server Error`: An unexpected error occurred.
