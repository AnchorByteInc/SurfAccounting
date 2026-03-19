<template>
  <div class="space-y-6">
    <Teleport to="#navbar-actions">
      <div class="pill-nav flex items-center">
        <button
          @click="router.push('/settings/users/new')"
          class="h-[40px] px-4 flex items-center justify-center rounded-full hover:bg-primary/8 gap-2 text-primary"
          title="Add User"
        >
          <span class="material-icons text-[20px]">person_add</span>
          <span class="text-sm font-medium">Add User</span>
        </button>
      </div>
    </Teleport>

    <!-- Table -->
    <div class="card p-0 overflow-hidden">
      <table class="standard-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Admin</th>
            <th>Status</th>
            <th class="text-right"></th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="user in users" 
            :key="user.id"
            class="hover:bg-primary/8"
          >
            <td class="whitespace-nowrap font-medium text-on-surface">{{ user.username }}</td>
            <td class="whitespace-nowrap text-muted">{{ user.email }}</td>
            <td class="whitespace-nowrap">
              <span v-if="user.is_admin" class="material-icons text-primary text-[20px]">check_circle</span>
            </td>
            <td class="whitespace-nowrap">
              <span 
                class="px-2 py-1 rounded-full text-xs font-bold"
                :class="user.is_active ? 'bg-success/20 text-success' : 'bg-error/20 text-error'"
              >
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="whitespace-nowrap text-right">
              <div class="flex justify-end gap-2">
                <button
                  @click.stop="confirmDelete(user)"
                  class="p-2 hover:bg-primary/8 rounded-full text-error"
                  title="Delete"
                  :disabled="isCurrentUser(user)"
                >
                  <span class="material-icons text-[20px]">delete</span>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="5" class="px-6 py-10 text-center text-muted">
              No users found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import userService from '../../services/userService';
import { useAuthStore } from '../../stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const users = ref([]);

const fetchUsers = async () => {
  try {
    const response = await userService.getUsers();
    users.value = response.data;
  } catch (error) {
    console.error('Failed to fetch users:', error);
  }
};

const isCurrentUser = (user) => {
  return authStore.user && authStore.user.username === user.username;
};

const confirmDelete = async (user) => {
  if (confirm(`Are you sure you want to delete user "${user.username}"?`)) {
    try {
      await userService.deleteUser(user.id);
      fetchUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('Failed to delete user.');
    }
  }
};

onMounted(() => {
  fetchUsers();
});
</script>
