<template>
  <v-container fluid>
    <!-- Main List Card (Always Visible) -->
    <v-card>
      <v-card-title class="d-flex align-center pe-2">
        <v-icon icon="mdi-map-marker" class="me-2"></v-icon>
        Destinations Management
        
        <v-spacer></v-spacer>

        <!-- Search Field -->
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          label="Search name"
          single-line
          flat
          hide-details
          variant="solo-filled"
          style="max-width: 300px;"
          class="me-2"
        ></v-text-field>

        <!-- Create Button -->
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">
          New Destination
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <!-- Data Table -->
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
        <!-- Status Column Customization -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="item.status === 'Active' ? 'green' : 'red'"
            size="small"
            class="text-uppercase"
          >
            {{ item.status }}
          </v-chip>
        </template>
        
        <!-- Created By Column -->
        <template v-slot:item.created_by_name="{ item }">
           {{ item.created_by_name || '-' }}
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-pencil" size="small" variant="text" color="primary" @click="openEdit(item)"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"></v-btn>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- FORM POPUP (Dialog) -->
    <v-dialog v-model="dialogForm" max-width="800px" persistent>
      <DestinationForm 
        v-if="dialogForm"
        :item-id="selectedId"
        @close="closeForm"
        @saved="onSaved"
      />
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="dialogDelete" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Are you sure?</v-card-title>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="dialogDelete = false">Cancel</v-btn>
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
import { ref } from 'vue';
import api from '@/api';
import DestinationForm from '@/form/DestinationForm.vue';

// State
const dialogForm = ref(false); // Controls form popup
const selectedId = ref(null);
const search = ref('');
const serverItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const itemsPerPage = ref(10);
const dialogDelete = ref(false);
const deletedItem = ref(null);

// Toast State
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
});

// Table Headers
const headers = [
  { title: 'ID', key: 'id', align: 'start' },
  { title: 'Name', key: 'name' },
  { title: 'Status', key: 'status' },
  { title: 'Created By', key: 'created_by_name', sortable: false },
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

// --- Actions ---

// 1. Open Create Popup
const openCreate = () => { 
  selectedId.value = null; 
  dialogForm.value = true; 
};

// 2. Open Edit Popup
const openEdit = (item) => { 
  selectedId.value = item.id; 
  dialogForm.value = true; 
};

// 3. Close Popup
const closeForm = () => { 
  dialogForm.value = false; 
  selectedId.value = null; 
};

// 4. Handle Save Success
const onSaved = () => { 
  closeForm(); 
  loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); 
  showToast('Destination saved successfully!', 'success');
};

// API Actions
const loadItems = async ({ page, itemsPerPage } = {}) => {
  const p = page || 1;
  const s = itemsPerPage || 10;
  loading.value = true;
  try {
    const response = await api.get('destinations/', {
      params: { page: p, page_size: s, search: search.value }
    });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) {
    console.error('Error:', error);
    showToast('Failed to load destinations', 'error');
  } finally {
    loading.value = false;
  }
};

const deleteItem = (item) => { 
  deletedItem.value = item; 
  dialogDelete.value = true; 
};

const deleteItemConfirm = async () => {
  try {
    await api.delete(`destinations/${deletedItem.value.id}/`);
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
    showToast('Destination deleted successfully!', 'success');
  } catch (e) { 
    console.error(e); 
    showToast('Failed to delete destination', 'error');
  } finally {
    dialogDelete.value = false;
  }
};
</script>