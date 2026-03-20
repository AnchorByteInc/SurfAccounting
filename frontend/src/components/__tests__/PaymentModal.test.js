import { mount, flushPromises } from "@vue/test-utils";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PaymentModal from "../PaymentModal.vue";
import paymentService from "../../services/paymentService";

vi.mock("../../services/paymentService");

describe("PaymentModal.vue", () => {
  const mockInvoice = {
    id: 1,
    invoice_number: "INV-001",
    balance: 500.5,
    customer_id: 10,
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("should not render when isOpen is false", () => {
    const wrapper = mount(PaymentModal, {
      props: {
        isOpen: false,
        invoice: mockInvoice,
      },
    });
    expect(wrapper.find(".modal-backdrop").exists()).toBe(false);
  });

  it("should render and pre-fill data when isOpen is true", async () => {
    const wrapper = mount(PaymentModal, {
      props: {
        isOpen: true,
        invoice: mockInvoice,
      },
    });

    expect(wrapper.find(".modal-backdrop").exists()).toBe(true);
    expect(wrapper.find("h2").text()).toContain("INV-001");

    const amountInput = wrapper.find('input[type="number"]');
    expect(amountInput.element.value).toBe("500.5");
  });

  it("should emit close when cancel is clicked", async () => {
    const wrapper = mount(PaymentModal, {
      props: {
        isOpen: true,
        invoice: mockInvoice,
      },
    });

    await wrapper.find('button[type="button"]').trigger("click");
    expect(wrapper.emitted()).toHaveProperty("close");
  });

  it("should submit payment and emit saved/close", async () => {
    paymentService.createPayment.mockResolvedValue({ data: { id: 1 } });

    const wrapper = mount(PaymentModal, {
      props: {
        isOpen: true,
        invoice: mockInvoice,
      },
    });

    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(paymentService.createPayment).toHaveBeenCalledWith(
      expect.objectContaining({
        invoice_id: 1,
        amount: 500.5,
        customer_id: 10,
      }),
    );
    expect(wrapper.emitted()).toHaveProperty("saved");
    expect(wrapper.emitted()).toHaveProperty("close");
  });
});
