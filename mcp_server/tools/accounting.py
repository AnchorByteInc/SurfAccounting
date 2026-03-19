from sqlalchemy import or_
from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from backend.models import Tax, Account
from backend.taxes.schemas import taxes_schema
from backend.accounts.schemas import accounts_schema
from mcp_server.utils.vector_store import search_accounts_semantic

# --- Section 3.2: Financial Configuration Lookups ---

@mcp.tool()
def get_taxes():
    """
    List all available tax rates and authorities.
    """
    try:
        with get_db_session() as session:
            taxes = session.query(Tax).all()
            return taxes_schema.dump(taxes)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_chart_of_accounts(type_filter: str = None):
    """
    List accounts from the chart of accounts, optionally filtered by type.
    Common types: Asset, Liability, Equity, Revenue, Expense.
    """
    try:
        with get_db_session() as session:
            query = session.query(Account)
            if type_filter:
                query = query.filter(Account.type == type_filter)
            accounts = query.order_by(Account.code).all()
            return accounts_schema.dump(accounts)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def search_accounts(query: str):
    """
    Find accounts by name or code for transaction coding.
    Uses semantic search for better discovery (e.g. "credit card" finds "Mastercard").
    """
    try:
        # Get semantic search results (account IDs)
        semantic_ids = search_accounts_semantic(query, top_k=20)
        
        with get_db_session() as session:
            # 1. Get accounts from semantic search
            semantic_accounts = []
            if semantic_ids:
                # We want to maintain the order from semantic search
                # SQLAlchemy's in_ doesn't preserve order, so we can fetch and then sort or use case
                unordered_accounts = session.query(Account).filter(Account.id.in_(semantic_ids)).all()
                account_map = {acc.id: acc for acc in unordered_accounts}
                semantic_accounts = [account_map[aid] for aid in semantic_ids if aid in account_map]

            # 2. Get keyword search results as fallback/supplement
            search_filter = or_(
                Account.name.ilike(f"%{query}%"),
                Account.code.ilike(f"%{query}%")
            )
            keyword_accounts = session.query(Account).filter(search_filter).all()

            # Merge results, keeping semantic results first and ensuring uniqueness
            seen_ids = set(acc.id for acc in semantic_accounts)
            final_accounts = list(semantic_accounts)
            for acc in keyword_accounts:
                if acc.id not in seen_ids:
                    final_accounts.append(acc)
                    seen_ids.add(acc.id)

            return accounts_schema.dump(final_accounts)
    except Exception as e:
        return f"Error: {str(e)}"
