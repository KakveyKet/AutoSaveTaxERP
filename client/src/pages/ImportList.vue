<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center pe-2">
        <v-icon icon="mdi-file-excel" class="me-2"></v-icon>
        Order Imports
        <v-spacer></v-spacer>
        
        <!-- Search Field -->
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          label="Search filename"
          single-line
          flat
          hide-details
          variant="solo-filled"
          style="max-width: 300px;"
          class="me-2"
          @update:model-value="loadItems({ page: 1, itemsPerPage })"
        ></v-text-field>

        <v-btn color="primary" prepend-icon="mdi-cloud-upload" @click="dialogUpload = true">
          Import New File
        </v-btn>
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
          <!-- 1. Run Bot -->
          <v-btn icon="mdi-robot" size="small" variant="text" color="orange" @click="runBot(item)"
            title="Auto Download Invoices" :loading="item.bot_status === 'running'"
            :disabled="item.bot_status === 'running'"></v-btn>

          <!-- 2. Download Result ZIP -->
          <v-btn v-if="item.generated_zip" icon="mdi-folder-zip" size="small" variant="text" color="success"
            :href="item.generated_zip" target="_blank" title="Download Invoices Zip"></v-btn>

          <v-btn icon="mdi-eye" size="small" variant="text" color="info" @click="viewDetails(item)"
            title="View Data"></v-btn>
          <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteItem(item)"
            title="Delete"></v-btn>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Dialogs (Upload, Details, Delete) -->
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
import { ref, onMounted, onUnmounted } from 'vue';
import api, { socket } from '@/api'; // Import socket
import ImportForm from '@/form/ImportForm.vue';

const dialogUpload = ref(false);
const dialogDetails = ref(false);
const dialogDelete = ref(false);
const selectedImport = ref(null);
const deletedItem = ref(null);
const search = ref('');
const serverItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const itemsPerPage = ref(10);
const snackbar = ref({ show: false, text: '', color: 'success' });

// Updated headers with sortable
const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: 'File Name', key: 'file', sortable: true },
  { title: 'Uploaded At', key: 'uploaded_at', sortable: true },
  // { title: 'Status', key: 'bot_status', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
];

const detailHeaders = [
  { title: 'Inv #', key: 'invoice_number' },
  { title: 'Customer', key: 'customer' },
  { title: 'Destination', key: 'destination' },
  { title: 'Forwarder', key: 'forwarder' },
];

// Updated loadItems with sorting & search
const loadItems = async ({ page, itemsPerPage, sortBy } = {}) => {
  const p = page || 1;
  const s = itemsPerPage || 10;
  
  let ordering = '';
  if (sortBy && sortBy.length > 0) {
      const { key, order } = sortBy[0];
      ordering = order === 'desc' ? `-${key}` : key;
  }

  loading.value = true;
  try {
    const response = await api.get('orders/', { 
      params: { 
        page: p, 
        page_size: s,
        search: search.value,
        ordering: ordering
      } 
    });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) { 
    console.error(error); 
    showToast('Failed to load data', 'error');
  }
  finally { loading.value = false; }
};

// --- RUN BOT ---
const runBot = async (item) => {
  try {
    item.bot_status = 'running'; // Optimistic update
    await api.post(`orders/${item.id}/run_bot/`);
    showToast('Auto-download started in background', 'info');
    // Socket will handle updates now
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

// --- SOCKET.IO INTEGRATION ---
onMounted(() => {
  if (!socket.connected) socket.connect();

  socket.on('order_update', (data) => {
    // console.log("Order Update:", data);
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
  });

  socket.on('bot_update', (data) => {
    // Optional: Could update specific row status directly for smoother UI
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
  });
});

onUnmounted(() => {
  socket.off('order_update');
  socket.off('bot_update');
});
</script>