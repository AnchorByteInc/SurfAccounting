<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <form @submit.prevent="handleSubmit" class="card space-y-4">
      <div class="form-group">
        <label class="form-label">Name *</label>
        <input
          v-model="form.name"
          type="text"
          required
          class="form-input"
          placeholder="Vendor name"
        />
        <p v-if="errors.name" class="text-error text-xs mt-1">
          {{ errors.name[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Primary Contact Name</label>
        <input
          v-model="form.primary_contact_name"
          type="text"
          class="form-input"
          placeholder="Primary contact name"
        />
        <p v-if="errors.primary_contact_name" class="text-error text-xs mt-1">
          {{ errors.primary_contact_name[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Email</label>
        <input
          v-model="form.email"
          type="email"
          class="form-input"
          placeholder="email@example.com"
        />
        <p v-if="errors.email" class="text-error text-xs mt-1">
          {{ errors.email[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Phone</label>
        <input
          v-model="form.phone"
          type="text"
          class="form-input"
          placeholder="Phone number"
        />
        <p v-if="errors.phone" class="text-error text-xs mt-1">
          {{ errors.phone[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Address</label>
        <textarea
          v-model="form.address"
          rows="3"
          class="form-input"
          placeholder="Street, City, Zip, Country"
        ></textarea>
        <p v-if="errors.address" class="text-error text-xs mt-1">
          {{ errors.address[0] }}
        </p>
      </div>

      <div class="pt-6 border-t border-divider flex justify-end">
        <button type="submit" :disabled="submitting" class="btn-primary">
          {{ submitting ? "Saving..." : "Save Vendor" }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import vendorService from "../../services/vendorService";

const route = useRoute();
const router = useRouter();

const isEdit = computed(() => !!route.params.id);
const submitting = ref(false);
const errors = ref({});

const form = ref({
  name: "",
  primary_contact_name: "",
  email: "",
  phone: "",
  address: "",
});

const fetchVendor = async () => {
  if (!isEdit.value) return;
  try {
    const response = await vendorService.getVendor(route.params.id);
    const { name, primary_contact_name, email, phone, address } = response.data;
    form.value = {
      name,
      primary_contact_name: primary_contact_name || "",
      email: email || "",
      phone: phone || "",
      address: address || "",
    };
  } catch (error) {
    console.error("Failed to fetch vendor:", error);
    alert("Failed to load vendor data.");
    router.push("/vendors");
  }
};

const handleSubmit = async () => {
  submitting.value = true;
  errors.value = {};
  try {
    if (isEdit.value) {
      await vendorService.updateVendor(route.params.id, form.value);
    } else {
      await vendorService.createVendor(form.value);
    }
    router.push("/vendors");
  } catch (error) {
    if (error.response && error.response.status === 400) {
      errors.value = error.response.data;
    } else {
      console.error("Failed to save vendor:", error);
      alert("An error occurred while saving.");
    }
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchVendor);
</script>
