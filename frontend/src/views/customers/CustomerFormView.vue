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
          placeholder="Customer name"
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
        <label class="form-label">Website</label>
        <input
          v-model="form.website"
          type="text"
          class="form-input"
          placeholder="https://example.com"
        />
        <p v-if="errors.website" class="text-error text-xs mt-1">
          {{ errors.website[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Billing Address</label>
        <textarea
          v-model="form.billing_address"
          rows="3"
          class="form-input"
          placeholder="Street, City, Zip, Country"
        ></textarea>
        <p v-if="errors.billing_address" class="text-error text-xs mt-1">
          {{ errors.billing_address[0] }}
        </p>
      </div>

      <div class="form-group">
        <label class="form-label">Shipping Address</label>
        <textarea
          v-model="form.shipping_address"
          rows="3"
          class="form-input"
          placeholder="Street, City, Zip, Country"
        ></textarea>
        <p v-if="errors.shipping_address" class="text-error text-xs mt-1">
          {{ errors.shipping_address[0] }}
        </p>
      </div>

      <div class="pt-6 border-t border-divider flex justify-end">
        <button type="submit" :disabled="submitting" class="btn-primary">
          {{ submitting ? "Saving..." : "Save Customer" }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import customerService from "../../services/customerService";

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
  website: "",
  billing_address: "",
  shipping_address: "",
});

const fetchCustomer = async () => {
  if (!isEdit.value) return;
  try {
    const response = await customerService.getCustomer(route.params.id);
    const {
      name,
      primary_contact_name,
      email,
      phone,
      website,
      billing_address,
      shipping_address,
    } = response.data;
    form.value = {
      name,
      primary_contact_name: primary_contact_name || "",
      email: email || "",
      phone: phone || "",
      website: website || "",
      billing_address: billing_address || "",
      shipping_address: shipping_address || "",
    };
  } catch (error) {
    console.error("Failed to fetch customer:", error);
    alert("Failed to load customer data.");
    router.push("/customers");
  }
};

const handleSubmit = async () => {
  submitting.value = true;
  errors.value = {};
  try {
    if (isEdit.value) {
      await customerService.updateCustomer(route.params.id, form.value);
    } else {
      await customerService.createCustomer(form.value);
    }
    router.push("/customers");
  } catch (error) {
    if (error.response && error.response.status === 400) {
      errors.value = error.response.data;
    } else {
      console.error("Failed to save customer:", error);
      alert("An error occurred while saving.");
    }
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchCustomer);
</script>
