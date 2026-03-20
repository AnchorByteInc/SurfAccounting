from mcp_server.tools.accounting import get_taxes, get_chart_of_accounts, search_accounts
from backend.models import Tax, Account
from backend.extensions import db
from decimal import Decimal

def test_get_taxes():
    tax = Tax(name="VAT", rate=Decimal("0.15"))
    db.session.add(tax)
    db.session.commit()
    
    result = get_taxes()
    assert isinstance(result, list)
    assert any(t['name'] == "VAT" for t in result)

def test_get_chart_of_accounts():
    acc1 = Account(name="Cash", code="1000", type="Asset")
    acc2 = Account(name="Sales", code="4000", type="Revenue")
    db.session.add_all([acc1, acc2])
    db.session.commit()
    
    result = get_chart_of_accounts()
    assert len(result) == 2
    
    result = get_chart_of_accounts(type_filter="Asset")
    assert len(result) == 1
    assert result[0]['name'] == "Cash"

def test_search_accounts():
    acc1 = Account(name="Bank Account", code="1010", type="Asset")
    acc2 = Account(name="Petty Cash", code="1020", type="Asset")
    db.session.add_all([acc1, acc2])
    db.session.commit()
    
    result = search_accounts("Bank")
    assert len(result) >= 1
    assert result[0]['name'] == "Bank Account"
    
    result = search_accounts("1020")
    assert len(result) >= 1
    assert result[0]['name'] == "Petty Cash"
