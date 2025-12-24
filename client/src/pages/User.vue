<template>
  <v-container fluid>
    <v-alert v-if="accessDenied" type="error" variant="tonal" class="mb-4">You do not have permission.</v-alert>
    <v-card v-else>
      <v-card-title class="d-flex align-center pe-2">
        <v-icon icon="mdi-account-group" class="me-2"></v-icon>
        User Management
        <v-spacer></v-spacer>
        <v-text-field 
          v-model="search" prepend-inner-icon="mdi-magnify" density="compact" 
          label="Search username or email" single-line flat hide-details variant="solo-filled" 
          style="max-width: 300px;" class="me-2" @update:model-value="loadItems({ page: 1, itemsPerPage })"
        ></v-text-field>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">New User</v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-data-table-server
        v-model:items-per-page="itemsPerPage" :headers="headers" :items="serverItems" :items-length="totalItems"
        :loading="loading" :search="search" item-value="id" @update:options="loadItems"
      >
        <template v-slot:item.role="{ item }">
          <v-chip :color="getRoleColor(item.role)" size="small" class="text-uppercase font-weight-bold">{{ item.role }}</v-chip>
        </template>
        <template v-slot:item.status="{ item }">
          <v-switch v-model="item.status" color="success" hide-details density="compact" inset @change="toggleStatus(item)" :loading="item.loading"></v-switch>
        </template>
        <template v-slot:item.created_at="{ item }">{{ new Date(item.created_at).toLocaleDateString() }}</template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="openEdit(item)"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"></v-btn>
        </template>
      </v-data-table-server>
    </v-card>

    <v-dialog v-model="dialogForm" max-width="800px" persistent>
      <UserForm v-if="dialogForm" :user-id="selectedUserId" @close="closeForm" @saved="onUserSaved" />
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Delete User?</v-card-title>
        <v-card-text>This action cannot be undone.</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="closeDelete">Cancel</v-btn>
          <v-btn color="error" variant="text" @click="deleteItemConfirm">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Toast Notification (Snackbar) -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top"
      timeout="3000"
    >
      {{ snackbar.text }}
      <template v-slot:actions="{ isActive }">
        <v-btn variant="text" @click="isActive.value = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import UserForm from '@/form/UserForm.vue';
import api, { socket } from '@/api'; 

const dialogForm = ref(false);
const selectedUserId = ref(null);
const search = ref('');
const serverItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const itemsPerPage = ref(10);
const dialogDelete = ref(false);
const deletedItem = ref(null);
const accessDenied = ref(false);

// Toast State
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
});

const headers = [
  { title: 'ID', key: 'id', align: 'start', sortable: true },
  { title: 'Username', key: 'username', sortable: true },
  { title: 'Email', key: 'email', sortable: true },
  { title: 'Role', key: 'role', sortable: true },
  { title: 'Status', key: 'status', sortable: false }, 
  { title: 'Joined', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
];

// --- Helper: Show Toast ---
const showToast = (message, color = 'success') => {
  snackbar.value = {
    show: true,
    text: message,
    color: color
  };
};

const loadItems = async ({ page, itemsPerPage, sortBy } = {}) => {
  const p = page || 1;
  const s = itemsPerPage || 10;
  let ordering = '';
  if (sortBy && sortBy.length > 0) ordering = sortBy[0].order === 'desc' ? `-${sortBy[0].key}` : sortBy[0].key;

  loading.value = true;
  accessDenied.value = false;
  try {
    const response = await api.get('users/', { params: { page: p, page_size: s, search: search.value, ordering } });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) {
    if (error.response &&(error.response.status === 403 || error.response.status === 401)) {
        accessDenied.value = true;
        serverItems.value = [];
    } else {
        showToast('Failed to load users.', 'error');
    }
  } finally { loading.value = false; }
};

const openCreate = () => { selectedUserId.value = null; dialogForm.value = true; };
const openEdit = (item) => { selectedUserId.value = item.id; dialogForm.value = true; };
const closeForm = () => { dialogForm.value = false; selectedUserId.value = null; };

// Handle Save (Create or Update)
const onUserSaved = () => { 
    // Determine message based on if we had an ID before saving
    const message = selectedUserId.value 
      ? 'User updated successfully.' 
      : 'User created successfully.';

    closeForm(); 
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); 
    showToast(message, 'success'); 
};

const toggleStatus = async (item) => {
  item.loading = true;
  try {
    await api.patch(`users/${item.id}/`, { status: item.status });
    const statusMsg = item.status ? 'activated' : 'deactivated';
    showToast(`User ${statusMsg}.`, 'success');
  } catch (error) {
    item.status = !item.status; // Revert switch if failed
    showToast('Failed to update status.', 'error');
  } finally { item.loading = false; }
};

const deleteItem = (item) => { deletedItem.value = item; dialogDelete.value = true; };

const deleteItemConfirm = async () => {
  if (!deletedItem.value) return;

  try {
    await api.delete(`users/${deletedItem.value.id}/`);
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
    showToast('User deleted successfully.', 'success');
  } catch (error) { 
    showToast('Failed to delete user.', 'error'); 
  } finally {
    closeDelete();
  }
};

const closeDelete = () => { dialogDelete.value = false; nextTick(() => { deletedItem.value = null; }); };

const getRoleColor = (role) => {
  switch (role) {
    case 'admin': return 'purple';
    case 'user': return 'blue';
    case 'guest': return 'grey';
    default: return 'primary';
  }
};

onMounted(() => {
  if (!socket.connected) socket.connect();
  socket.on('user_update', () => loadItems({ page: 1, itemsPerPage: itemsPerPage.value }));
});
onUnmounted(() => { socket.off('user_update'); });
</script>