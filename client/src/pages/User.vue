<template>
  <v-container fluid>
    <!-- Access Denied Alert -->
    <v-alert v-if="accessDenied" type="error" variant="tonal" class="mb-4">
      You do not have permission to view or manage users.
    </v-alert>

    <v-card v-else>
      <v-card-title class="d-flex align-center pe-2">
        <v-icon icon="mdi-account-group" class="me-2"></v-icon>
        User Management
        <v-spacer></v-spacer>
        <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" density="compact" label="Search username or email" single-line flat hide-details variant="solo-filled" style="max-width: 300px;" class="me-2"></v-text-field>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">New User</v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-data-table-server
        v-model:items-per-page="itemsPerPage"
        :headers="headers"
        :items="serverItems"
        :items-length="totalItems"
        :loading="loading"
        :search="search"
        item-value="id"
        @update:options="loadItems"
      >
        <template v-slot:item.role="{ item }">
          <v-chip :color="getRoleColor(item.role)" size="small" class="text-uppercase font-weight-bold">{{ item.role }}</v-chip>
        </template>
        <template v-slot:item.status="{ item }">
          <v-switch v-model="item.status" color="success" hide-details density="compact" inset @change="toggleStatus(item)" :loading="item.loading"></v-switch>
        </template>
        <template v-slot:item.created_at="{ item }">
            {{ new Date(item.created_at).toLocaleDateString() }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="openEdit(item)"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"></v-btn>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Dialogs -->
    <v-dialog v-model="dialogForm" max-width="800px" persistent>
      <UserForm v-if="dialogForm" :user-id="selectedUserId" @close="closeForm" @saved="onUserSaved" />
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Delete User?</v-card-title>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="closeDelete">Cancel</v-btn>
          <v-btn color="blue-darken-1" variant="text" @click="deleteItemConfirm">OK</v-btn>
          <v-spacer></v-spacer>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">{{ snackbar.text }}</v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import UserForm from '@/form/UserForm.vue';
import api from '@/api';

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

const snackbar = ref({ show: false, text: '', color: 'success' });
const showToast = (message, color = 'success') => { snackbar.value = { show: true, text: message, color: color }; };

const headers = [
  { title: 'ID', key: 'id', align: 'start' },
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Role', key: 'role' },
  { title: 'Status', key: 'status' }, 
  { title: 'Joined', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const loadItems = async ({ page, itemsPerPage } = {}) => {
  loading.value = true;
  accessDenied.value = false;
  try {
    const response = await api.get('users/', {
      params: { page, page_size: itemsPerPage, search: search.value },
    });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) {
    if (error.response &&(error.response.status === 403 || error.response.status === 401)) {
        accessDenied.value = true;
        serverItems.value = [];
    } else {
        console.error('Error fetching users:', error);
        showToast('Failed to load users', 'error');
    }
  } finally {
    loading.value = false;
  }
};

const openCreate = () => { selectedUserId.value = null; dialogForm.value = true; };
const openEdit = (item) => { selectedUserId.value = item.id; dialogForm.value = true; };
const closeForm = () => { dialogForm.value = false; selectedUserId.value = null; };
const onUserSaved = () => { closeForm(); loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); showToast('User saved successfully!', 'success'); };

const toggleStatus = async (item) => {
  item.loading = true;
  try {
    await api.patch(`users/${item.id}/`, { status: item.status });
    showToast(`User ${item.status ? 'activated' : 'deactivated'}`, 'info');
  } catch (error) {
    console.error('Error updating status:', error);
    item.status = !item.status; 
    showToast('Failed to update status', 'error');
  } finally {
    item.loading = false;
  }
};

const deleteItem = (item) => { deletedItem.value = item; dialogDelete.value = true; };
const deleteItemConfirm = async () => {
  try {
    await api.delete(`users/${deletedItem.value.id}/`);
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
    showToast('User deleted successfully!', 'success');
  } catch (error) {
    console.error('Error deleting user:', error);
    showToast('Failed to delete user', 'error');
  }
  closeDelete();
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
</script>