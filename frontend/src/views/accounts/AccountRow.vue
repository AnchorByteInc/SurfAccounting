<template>
  <tr
    @click="editAccount(account.id)"
    class="cursor-pointer hover:bg-primary/8"
  >
    <td class="whitespace-nowrap font-medium text-on-surface">
      <span :style="{ marginLeft: `${level * 24}px` }">{{ account.code }}</span>
    </td>
    <td class="whitespace-nowrap">
      <span
        :class="{
          'font-bold': account.children && account.children.length > 0,
        }"
        >{{ account.name }}</span
      >
    </td>
    <td class="whitespace-nowrap text-muted">{{ account.type }}</td>
    <td class="whitespace-nowrap text-muted">{{ account.subtype || "-" }}</td>
    <td class="whitespace-nowrap">
      <span
        class="badge"
        :class="
          account.is_active ? 'bg-green-100 text-green-700' : 'badge-primary'
        "
      >
        {{ account.is_active ? "Active" : "Inactive" }}
      </span>
      <span v-if="account.is_system" class="badge bg-gray-100 text-muted ml-2"
        >System</span
      >
    </td>
    <td class="whitespace-nowrap text-right">
      <div class="flex justify-end gap-2">
        <RouterLink
          :to="`/settings/accounts/${account.id}/edit`"
          @click.stop
          class="p-2 hover:bg-primary/8 rounded-full text-primary"
          title="Edit"
        >
          <span class="material-icons text-[20px]">edit</span>
        </RouterLink>
        <button
          v-if="!account.is_system"
          @click.stop="confirmDelete(account)"
          class="p-2 hover:bg-primary/8 rounded-full text-error"
          title="Delete"
        >
          <span class="material-icons text-[20px]">delete</span>
        </button>
      </div>
    </td>
  </tr>
  <template v-if="account.children && account.children.length > 0">
    <AccountRow
      v-for="child in account.children"
      :key="child.id"
      :account="child"
      :level="level + 1"
      @refresh="$emit('refresh')"
    />
  </template>
</template>

<script setup>
import { RouterLink, useRouter } from "vue-router";
import accountService from "../../services/accountService";

const props = defineProps({
  account: {
    type: Object,
    required: true,
  },
  level: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(["refresh"]);

const router = useRouter();

const editAccount = (id) => {
  router.push(`/settings/accounts/${id}/edit`);
};

const confirmDelete = async (account) => {
  if (confirm(`Are you sure you want to delete account "${account.name}"?`)) {
    try {
      await accountService.deleteAccount(account.id);
      emit("refresh");
    } catch (error) {
      console.error("Failed to delete account:", error);
      alert(
        error.response?.data?.message ||
          error.response?.data?.msg ||
          "Failed to delete account.",
      );
    }
  }
};
</script>

<script>
// Recursive component name
export default {
  name: "AccountRow",
};
</script>
