<template>
  <div class="max-w-2xl mx-auto">
    <div class="card">
      <h2 class="mb-6">Add New User</h2>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            v-model="user.username"
            id="username"
            type="text"
            required
            class="form-input"
            placeholder="Enter username"
          />
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input
            v-model="user.email"
            id="email"
            type="email"
            required
            class="form-input"
            placeholder="Enter email address"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            v-model="user.password"
            id="password"
            type="password"
            required
            class="form-input"
            placeholder="Enter password"
          />
        </div>

        <div class="flex items-center gap-2 py-2">
          <input
            v-model="user.is_admin"
            id="is_admin"
            type="checkbox"
            class="rounded text-primary focus:ring-primary"
          />
          <label for="is_admin" class="text-sm font-medium">Administrator Access</label>
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
            {{ submitting ? 'Saving...' : 'Create User' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import userService from '../../services/userService';

const router = useRouter();
const submitting = ref(false);

const user = ref({
  username: '',
  email: '',
  password: '',
  is_admin: false,
  is_active: true
});

const handleSubmit = async () => {
  submitting.value = true;
  try {
    await userService.createUser(user.value);
    router.push('/settings/users');
  } catch (error) {
    console.error('Failed to create user:', error);
    alert(error.response?.data?.message || 'Failed to create user.');
  } finally {
    submitting.value = false;
  }
};
</script>
