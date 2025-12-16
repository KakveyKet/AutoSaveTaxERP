<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center pe-2">
        <v-icon icon="mdi-file-excel" class="me-2"></v-icon>
        Order Imports
        <v-spacer></v-spacer>
        <v-btn color="primary" prepend-icon="mdi-cloud-upload" @click="dialogUpload = true">
          Import New File
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-data-table-server v-model:items-per-page="itemsPerPage" :headers="headers" :items="serverItems"
        :items-length="totalItems" :loading="loading" item-value="id" @update:options="loadItems">
        <template v-slot:item.file="{ item }">
          <span class="font-weight-medium text-truncate" style="max-width: 200px; display: block;">
            {{ getFileName(item.file) }}
          </span>
        </template>

        <template v-slot:item.uploaded_at="{ item }">
          {{ new Date(item.uploaded_at).toLocaleString() }}
        </template>

        <!-- Bot Status Column -->
        <template v-slot:item.bot_status="{ item }">
          <v-chip :color="getBotColor(item.bot_status)" size="small" class="text-uppercase">
            {{ item.bot_status }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <!-- 1. Download Original -->
          <!-- <v-btn icon="mdi-download" size="small" variant="text" color="primary" :href="item.file" target="_blank"
            title="Download Excel"></v-btn> -->

          <!-- 2. Run Bot -->
          <v-btn icon="mdi-robot" size="small" variant="text" color="orange" @click="runBot(item)"
            title="Auto Download Invoices" :loading="item.bot_status === 'running'"
            :disabled="item.bot_status === 'running'"></v-btn>

          <!-- 3. Download Result ZIP -->
          <v-btn v-if="item.generated_zip" icon="mdi-folder-zip" size="small" variant="text" color="success"
            :href="item.generated_zip" target="_blank" title="Download Invoices Zip"></v-btn>

          <v-btn icon="mdi-eye" size="small" variant="text" color="info" @click="viewDetails(item)"
            title="View Data"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"
            title="Delete"></v-btn>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Dialogs (Upload, Details, Delete) - Keeping existing ones -->
    <v-dialog v-model="dialogUpload" max-width="500px">
      <ImportForm @close="dialogUpload = false" @saved="onUploaded" />
    </v-dialog>

    <v-dialog v-model="dialogDetails" fullscreen transition="dialog-bottom-transition">
      <v-card>
        <v-toolbar color="primary">
          <v-btn icon @click="dialogDetails = false"><v-icon>mdi-close</v-icon></v-btn>
          <v-toolbar-title>Details</v-toolbar-title>
        </v-toolbar>
        <v-card-text>
          <v-data-table v-if="selectedImport?.parsed_data" :items="selectedImport.parsed_data" :headers="detailHeaders"
            density="compact"></v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="400px">
      <v-card>
        <v-card-title class="text-h6">Delete?</v-card-title>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialogDelete = false">Cancel</v-btn>
          <v-btn color="error" text @click="deleteItemConfirm">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color">{{ snackbar.text }}</v-snackbar>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import api from '@/api';
import ImportForm from '@/form/ImportForm.vue';

const dialogUpload = ref(false);
const dialogDetails = ref(false);
const dialogDelete = ref(false);
const selectedImport = ref(null);
const deletedItem = ref(null);
const serverItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const itemsPerPage = ref(10);
const snackbar = ref({ show: false, text: '', color: 'success' });

const headers = [
  { title: 'ID', key: 'id', sortable: false },
  { title: 'File Name', key: 'file', sortable: false },
  { title: 'Uploaded At', key: 'uploaded_at' },
  // { title: 'Status', key: 'bot_status' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const detailHeaders = [
  { title: 'Inv #', key: 'invoice_number' },
  { title: 'Customer', key: 'customer' },
  { title: 'Destination', key: 'destination' },
  { title: 'Forwarder', key: 'forwarder' },
];

const loadItems = async ({ page, itemsPerPage }) => {
  loading.value = true;
  try {
    const response = await api.get('orders/', { params: { page, page_size: itemsPerPage } });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) { console.error(error); }
  finally { loading.value = false; }
};

// --- NEW FUNCTION: RUN BOT ---
const runBot = async (item) => {
  try {
    item.bot_status = 'running'; // Optimistic update
    await api.post(`orders/${item.id}/run_bot/`);
    showToast('Auto-download started in background', 'info');
    // Poll for status or just wait for reload
  } catch (error) {
    console.error('Bot start error:', error);
    showToast('Failed to start bot', 'error');
    item.bot_status = 'failed';
  }
};

const getBotColor = (status) => {
  if (status === 'completed') return 'success';
  if (status === 'running') return 'warning';
  if (status === 'failed') return 'error';
  return 'grey';
};

const onUploaded = () => { dialogUpload.value = false; loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); showToast('File processed!'); };
const viewDetails = (item) => { selectedImport.value = item; dialogDetails.value = true; };
const deleteItem = (item) => { deletedItem.value = item; dialogDelete.value = true; };
const deleteItemConfirm = async () => { await api.delete(`orders/${deletedItem.value.id}/`); loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); dialogDelete.value = false; };
const getFileName = (path) => path ? path.split('/').pop() : '';
const showToast = (text, color = 'success') => { snackbar.value = { show: true, text, color }; };
</script>