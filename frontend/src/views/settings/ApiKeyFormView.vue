<template>
  <div class="max-w-2xl mx-auto">
    <div class="card">
      <h2 class="mb-6">Create API Key</h2>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="form-group">
          <label for="name">Name</label>
          <input
            v-model="apiKey.name"
            id="name"
            type="text"
            required
            class="form-input"
            placeholder="e.g. MCP Server, CI/CD Pipeline"
          />
        </div>

        <div class="form-group">
          <label for="expires_at">Expiration (optional)</label>
          <input
            v-model="apiKey.expires_at"
            id="expires_at"
            type="date"
            class="form-input"
            :min="minDate"
          />
        </div>

        <div class="flex justify-end gap-3 pt-4">
          <button
            type="button"
            @click="router.back()"
            class="px-6 py-2 rounded-full border border-divider hover:bg-surface-variant font-medium"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-6 py-2 rounded-full bg-primary text-white font-medium hover:opacity-90 disabled:opacity-50"
            :disabled="submitting"
          >
            {{ submitting ? "Creating..." : "Create API Key" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import apiKeyService from "../../services/apiKeyService";

const router = useRouter();
const submitting = ref(false);

const apiKey = ref({
  name: "",
  expires_at: "",
});

const minDate = computed(() => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().split("T")[0];
});

const handleSubmit = async () => {
  submitting.value = true;
  try {
    const payload = { name: apiKey.value.name };
    if (apiKey.value.expires_at) {
      payload.expires_at = new Date(apiKey.value.expires_at).toISOString();
    }
    const response = await apiKeyService.createApiKey(payload);
    router.push({
      path: "/settings/api-keys",
      query: { newKey: response.data.key },
    });
  } catch (error) {
    console.error("Failed to create API key:", error);
    alert(error.response?.data?.message || "Failed to create API key.");
  } finally {
    submitting.value = false;
  }
};
</script>
