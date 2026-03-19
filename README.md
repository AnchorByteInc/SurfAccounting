# Surf Accounting

Surf Accounting is a full-featured, lightweight bookkeeping and invoicing application designed for small businesses and freelancers. It features a robust Flask-based REST API and a modern, responsive Vue.js frontend.

## Features

- **Dashboard**: Get a quick overview of your financial health.
- **Invoicing & Billing**: Create, manage, and track invoices for customers and bills from vendors.
- **Customer & Vendor Management**: Keep track of your business relationships.
- **Chart of Accounts**: Customize your accounting structure.
- **General Journal**: Record and manage manual journal entries.
- **Bank Accounts**: Manage multiple bank accounts and track balances.
- **Payments**: Record payments against invoices and bills.
- **Reports**: Generate essential financial reports (Balance Sheet, Profit & Loss).
- **Taxes**: Manage tax rates and tracking.
- **MCP Server**: Integrated Model Context Protocol server for AI-assisted accounting tasks.

## Tech Stack

### Backend
- **Framework**: [Flask](https://flask.palletsprojects.com/)
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) with SQLite (default)
- **Migrations**: [Flask-Migrate](https://flask-migrate.readthedocs.io/)
- **Authentication**: [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- **Serialization**: [Marshmallow](https://marshmallow.readthedocs.io/)

### Frontend
- **Framework**: [Vue.js 3](https://vuejs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **State Management**: [Pinia](https://pinia.vuejs.org/)
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/)
- **Components**: [Material Web Components](https://github.com/material-components/material-web)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Charts**: [Chart.js](https://www.chartjs.org/)

## Getting Started

### Prerequisites
- **Python**: 3.13 or higher
- **Node.js**: v18 or higher
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (recommended for Python) or `pip`

### Backend Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/SurfAccounting.git
    cd SurfAccounting
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *Alternatively, if you use `uv`:*
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -e .
    ```
    *Alternatively, if you use `uv`:*
    ```bash
    uv sync
    ```

4.  **Configure environment variables**:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to set your secret keys and other settings.

5.  **Initialize the database**:
    ```bash
    python3 scripts/reset_db.py
    ```

6.  **Run the backend server**:
    ```bash
    python3 -m backend.app
    ```
    The API will be available at `http://localhost:5001`.

### Frontend Setup

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Run the development server**:
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`.

### MCP Server

Surf Accounting includes an MCP (Model Context Protocol) server that allows AI agents to interact with your accounting data securely.

To start the MCP server:
```bash
python3 -m mcp_server.server
```
For more detailed information on setup and usage, see the [mcp_server/README.md](mcp_server/README.md).

## Running with Docker

You can run the entire application (Frontend and Backend) using Docker:

1.  **Build the Docker image**:
    ```bash
    docker build -t surf-accounting .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8080:80 \
      -e SECRET_KEY=your_secret_key \
      -e JWT_SECRET_KEY=your_jwt_secret_key \
      --name surf-accounting \
      surf-accounting
    ```
    The application will be available at `http://localhost:8080`.

3.  **Persisting Data**:
    To persist the database and uploads, mount a volume:
    ```bash
    docker run -p 8080:80 \
      -v $(pwd)/data.sqlite:/app/data.sqlite \
      -v $(pwd)/uploads:/app/uploads \
      -e SECRET_KEY=your_secret_key \
      -e JWT_SECRET_KEY=your_jwt_secret_key \
      --name surf-accounting \
      surf-accounting
    ```

## Administrative Utilities

### Database Regeneration

If the database (`data.sqlite`) is deleted or needs to be reset, use the `scripts/reset_db.py` script:
```bash
python3 scripts/reset_db.py --force
```

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

To report security vulnerabilities, please see our [SECURITY.md](SECURITY.md).

## License

This project is licensed under the terms of the MIT license.
