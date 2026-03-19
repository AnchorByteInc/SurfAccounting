import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import InvoiceFormView from '../InvoiceFormView.vue'
import invoiceService from '../../../services/invoiceService'
import customerService from '../../../services/customerService'
import accountService from '../../../services/accountService'
import settingsService from '../../../services/settingsService'
import { useRouter, useRoute } from 'vue-router'

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
  useRoute: vi.fn(() => ({
    params: {},
  })),
  RouterLink: {
    template: '<a><slot /></a>',
  },
}))

vi.mock('../../../services/invoiceService')
vi.mock('../../../services/customerService')
vi.mock('../../../services/accountService')
vi.mock('../../../services/settingsService')

describe('InvoiceFormView.vue', () => {
  const mockCustomers = [
    { id: 1, name: 'Customer A' },
    { id: 2, name: 'Customer B' },
  ]
  const mockAccounts = [
    { id: 1, code: '4000', name: 'Sales' },
    { id: 2, code: '4001', name: 'Other Revenue' },
  ]
  const mockSettings = {
    settings: [{ tax_rate: '0.1' }], // 10% tax
  }

  beforeEach(() => {
    vi.resetAllMocks()
    customerService.getCustomers.mockResolvedValue({ data: { customers: mockCustomers } })
    accountService.getAccounts.mockResolvedValue({ data: { accounts: mockAccounts } })
    settingsService.getSettingsList.mockResolvedValue({ data: mockSettings })
  })

  it('should render the form with initial values', async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ['RouterLink'],
      },
    })
    await flushPromises()

    expect(wrapper.find('h3').text()).toBe('Invoice Lines')
    expect(wrapper.find('select').exists()).toBe(true)
    // Initially has 1 line
    expect(wrapper.findAll('tbody tr').length).toBe(1)
  })

  it('should calculate totals correctly', async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ['RouterLink'],
      },
    })
    await flushPromises()

    const qtyInput = wrapper.find('input[type="number"]')
    const priceInput = wrapper.findAll('input[type="number"]')[1]

    await qtyInput.setValue(2)
    await priceInput.setValue(100)

    // subtotal = 2 * 100 = 200
    // tax = 200 * 0.1 = 20
    // total = 220
    
    // Check totals in the UI
    const subtotalText = wrapper.text()
    expect(subtotalText).toContain('200.00')
    expect(subtotalText).toContain('20.00')
    expect(subtotalText).toContain('220.00')
  })

  it('should add and remove lines', async () => {
    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ['RouterLink'],
      },
    })
    await flushPromises()

    // Add a line
    const addButton = wrapper.findAll('button').find(b => b.text().includes('Add Line Item'))
    await addButton.trigger('click')
    expect(wrapper.findAll('tbody tr').length).toBe(2)

    // Remove a line
    const removeButton = wrapper.find('button[title="Remove"]')
    await removeButton.trigger('click')
    expect(wrapper.findAll('tbody tr').length).toBe(1)
  })

  it('should submit the form correctly', async () => {
    const mockRouter = { push: vi.fn() }
    useRouter.mockReturnValue(mockRouter)
    invoiceService.createInvoice.mockResolvedValue({ data: { id: 123 } })

    const wrapper = mount(InvoiceFormView, {
      global: {
        stubs: ['RouterLink'],
      },
    })
    await flushPromises()

    // Fill the form
    await wrapper.find('select').setValue(1)
    await wrapper.findAll('input')[0].setValue('INV-2026-001')
    
    const lineDesc = wrapper.find('table input[type="text"]')
    await lineDesc.setValue('Test Item')
    
    const qtyInput = wrapper.find('input[type="number"]')
    await qtyInput.setValue(1)
    
    const priceInput = wrapper.findAll('input[type="number"]')[1]
    await priceInput.setValue(500)

    // Set account
    const accountSelect = wrapper.findAll('table select')[0]
    await accountSelect.setValue(1)

    // Submit
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(invoiceService.createInvoice).toHaveBeenCalled()
    expect(mockRouter.push).toHaveBeenCalledWith('/invoices')
  })
})
