import { mount, flushPromises } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";
import { describe, it, expect, vi, beforeEach } from "vitest";
import LoginView from "../LoginView.vue";
import { useAuthStore } from "../../stores/auth";
import { useRouter } from "vue-router";

const mockPush = vi.fn();
vi.mock("vue-router", () => ({
  useRouter: vi.fn(() => ({
    push: mockPush,
  })),
}));

describe("LoginView.vue", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });
  it("should render the login form correctly", () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [createTestingPinia()],
      },
    });
    expect(wrapper.find("h2").text()).toBe("Sign in to your account");
    expect(wrapper.find("input#username").exists()).toBe(true);
    expect(wrapper.find("input#password").exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').text()).toBe("Sign in");
  });

  it("should call login on form submit", async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
          }),
        ],
      },
    });
    const authStore = useAuthStore();
    const router = useRouter();

    await wrapper.find("input#username").setValue("testadmin");
    await wrapper.find("input#password").setValue("testpass");
    await wrapper.find("form").trigger("submit.prevent");

    expect(authStore.login).toHaveBeenCalledWith("testadmin", "testpass");
  });

  it("should redirect to home on successful login", async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            stubActions: false, // We need to handle the promise
          }),
        ],
      },
    });
    const authStore = useAuthStore();
    const router = useRouter();

    // Mock successful login
    authStore.login = vi.fn().mockResolvedValue();

    await wrapper.find("input#username").setValue("testadmin");
    await wrapper.find("input#password").setValue("testpass");
    await wrapper.find("form").trigger("submit.prevent");

    await flushPromises();

    expect(authStore.login).toHaveBeenCalled();
    expect(router.push).toHaveBeenCalledWith("/");
  });

  it("should show error message on failed login", async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            stubActions: false,
          }),
        ],
      },
    });
    const authStore = useAuthStore();

    // Mock failed login
    authStore.login = vi
      .fn()
      .mockRejectedValue(new Error("Invalid username or password"));

    await wrapper.find("input#username").setValue("testadmin");
    await wrapper.find("input#password").setValue("wrongpass");
    await wrapper.find("form").trigger("submit.prevent");

    // Wait for async operations
    await flushPromises();

    expect(wrapper.find(".text-error").exists()).toBe(true);
    expect(wrapper.find(".text-error").text()).toBe(
      "Invalid username or password",
    );
  });
});
