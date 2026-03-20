import { mount, flushPromises } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import InvoiceFormView from "../InvoiceFormView.vue";
import invoiceService from "../../../services/invoiceService";
import customerService from "../../../services/customerService";
import accountService from "../../../services/accountService";
import taxService from "../../../services/taxService";
import itemService from "../../../services/itemService";
import { useRouter, useRoute } from "vue-router";

vi.mock("vue-router", () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
  useRoute: vi.fn(() => ({
    params: {},
  })),
  RouterLink: {
    template: "<a><slot /></a>",
  },
}));

vi.mock("../../../services/invoiceService");
vi.mock("../../../services/customerService");
vi.mock("../../../services/accountService");
vi.mock("../../../services/taxService");
vi.mock("../../../services/itemService");

describe("InvoiceFormView.vue", () => {
  const mockCustomers = [
    { id: 1, name: "Customer A" },
    { id: 2, name: "Customer B" },
  ];
  const mockAccounts = [
    { id: 1, code: "4000", name: "Sales" },
    { id: 2, code: "4001", name: "Other Revenue" },
  ];
  const mockTaxes = [
    { id: 1, name: "VAT", rate: "0.1" },
  ];
  const mockItems = [
    { id: 1, name: "Test Item", price: "100", income_account_id: 1, sales_taxes: [{id: 1}] },
  ];

  beforeEach(() => {
    // Create a teleport target
    const el = document.createElement('div')
    el.id = 'navbar-actions'
    document.body.appendChild(el)

    vi.resetAllMocks();
    customerService.getCustomers.mockResolvedValue({
      data: { customers: mockCustomers },
    });
    accountService.getAccounts.mockResolvedValue({
      data: { accounts: mockAccounts },
    });
    taxService.getTaxes.mockResolvedValue({
      data: { taxes: mockTaxes },
    });
    itemService.getItems.mockResolvedValue({
      data: { items: mockItems },
    });
  });

  afterEach(() => {
    const el = document.getElementById('navbar-actions')
    if (el) {
      document.body.removeChild(el)
    }
  })

  it("should render the form with initial values", async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ["RouterLink", "PaymentModal"],
      },
    });
    await flushPromises();

    expect(wrapper.find("h3").text()).toBe("Invoice Lines");
    expect(wrapper.find("select").exists()).toBe(true);
    // Initially has 1 line
    expect(wrapper.findAll("tbody tr").length).toBe(1);
  });

  it("should calculate totals correctly", async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ["RouterLink", "PaymentModal"],
      },
    });
    await flushPromises();

    const qtyInput = wrapper.find('input[type="number"]');
    const priceInput = wrapper.findAll('input[type="number"]')[1];

    await qtyInput.setValue(2);
    await priceInput.setValue(100);
    
    // Select an item that has tax
    const itemSelect = wrapper.find('table select');
    await itemSelect.setValue(1);
    await flushPromises();

    // Check totals in the UI
    const subtotalText = wrapper.text();
    expect(subtotalText).toContain("200.00");
    expect(subtotalText).toContain("20.00");
    expect(subtotalText).toContain("220.00");
  });

  it("should add and remove lines", async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ["RouterLink", "PaymentModal"],
      },
    });
    await flushPromises();

    // Add a line
    const addButton = wrapper
      .findAll("button")
      .find((b) => b.text().includes("Add Line Item"));
    await addButton.trigger("click");
    expect(wrapper.findAll("tbody tr").length).toBe(2);

    // Remove a line
    const removeButton = wrapper.find('button[title="Remove"]');
    await removeButton.trigger("click");
    expect(wrapper.findAll("tbody tr").length).toBe(1);
  });

  it("should submit the form correctly", async () => {
    const mockRouter = { push: vi.fn() };
    useRouter.mockReturnValue(mockRouter);
    invoiceService.createInvoice.mockResolvedValue({ data: { id: 123 } });

    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ["RouterLink", "PaymentModal"],
      },
    });
    await flushPromises();

    // Fill the form
    await wrapper.find("select").setValue(1); // Customer
    await wrapper.findAll("input")[0].setValue("INV-2026-001"); // Invoice Number

    // Selection of item
    const itemSelect = wrapper.findAll("table select")[0];
    await itemSelect.setValue(1);
    await flushPromises();

    // Submit
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(invoiceService.createInvoice).toHaveBeenCalled();
    expect(mockRouter.push).toHaveBeenCalledWith("/invoices");
  });
});
