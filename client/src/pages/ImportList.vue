<template>
  <v-container fluid class="pa-6">
    <v-card class="elevation-2 rounded-lg">
      <!-- 1. Header Section -->
      <v-card-title class="d-flex align-center py-4 px-6 bg-primary text-white">
        <v-icon icon="mdi-file-excel-box" class="me-3" size="large"></v-icon>
        <span class="text-h6 font-weight-bold">Order Imports Management</span>
        <v-spacer></v-spacer>
        <v-btn 
          color="white" 
          variant="elevated" 
          class="text-primary font-weight-bold"
          prepend-icon="mdi-cloud-upload" 
          @click="dialogUpload = true"
        >
          Import New File
        </v-btn>
      </v-card-title>

      <!-- 2. Filter & Search Toolbar -->
      <v-card-text class="pt-6 pb-2 px-6">
        <v-row align="center" dense>
          <!-- Period Filter -->
          <v-col cols="12" md="auto" class="d-flex align-center py-2">
            <span class="text-subtitle-2 mr-3 text-medium-emphasis">Filter by Date:</span>
            <v-btn-toggle
              v-model="selectedPeriod"
              color="primary"
              variant="outlined"
              density="compact"
              divided
              mandatory
              class="rounded-md"
              @update:model-value="onPeriodChange"
            >
              <v-btn value="" class="text-caption">All</v-btn>
              <v-btn value="daily" class="text-caption">Today</v-btn>
              <v-btn value="weekly" class="text-caption">Week</v-btn>
              <v-btn value="monthly" class="text-caption">Month</v-btn>
              <v-btn value="custom" class="text-caption">Custom</v-btn>
            </v-btn-toggle>
          </v-col>

          <!-- Custom Date Range Inputs (Conditional) -->
          <v-col cols="12" md="auto" v-if="selectedPeriod === 'custom'" class="py-2">
            <div class="d-flex align-center gap-2">
              <v-text-field
                v-model="startDate"
                type="date"
                label="Start Date"
                density="compact"
                variant="outlined"
                hide-details
                bg-color="white"
                style="width: 140px"
              ></v-text-field>
              <span class="text-grey mx-1">-</span>
              <v-text-field
                v-model="endDate"
                type="date"
                label="End Date"
                density="compact"
                variant="outlined"
                hide-details
                bg-color="white"
                style="width: 140px"
              ></v-text-field>
              <v-btn 
                color="primary" 
                variant="tonal" 
                icon="mdi-check" 
                density="comfortable"
                class="ml-2"
                @click="refreshData"
                title="Apply Filter"
              ></v-btn>
            </div>
          </v-col>
          
          <v-spacer class="hidden-sm-and-down"></v-spacer>

          <!-- Search Field -->
          <v-col cols="12" md="4" lg="3" class="py-2">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              density="compact"
              label="Search filename..."
              variant="outlined"
              hide-details
              bg-color="white"
              clearable
              @update:model-value="loadItems({ page: 1, itemsPerPage })"
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-text>

      <v-divider></v-divider>

      <!-- 3. Data Table -->
      <v-data-table-server 
        v-model:items-per-page="itemsPerPage" 
        :headers="headers" 
        :items="serverItems"
        :items-length="totalItems" 
        :loading="loading" 
        :search="search"
        item-value="id" 
        @update:options="loadItems"
        class="px-4 pb-4"
        hover
      >
        <!-- File Name -->
        <template v-slot:item.file="{ item }">
          <div class="d-flex align-center py-2">
            <v-icon icon="mdi-file-document-outline" color="grey" class="mr-2"></v-icon>
            <span class="font-weight-medium text-body-2 text-truncate" style="max-width: 250px;" :title="getFileName(item.file)">
              {{ getFileName(item.file) }}
            </span>
          </div>
        </template>

        <!-- Uploaded At -->
        <template v-slot:item.uploaded_at="{ item }">
          <span class="text-caption text-grey-darken-1">
            {{ new Date(item.uploaded_at).toLocaleString() }}
          </span>
        </template>

        <!-- Bot Status Column -->
        <template v-slot:item.bot_status="{ item }">
          <v-chip 
            :color="getBotColor(item.bot_status)" 
            size="x-small" 
            label
            class="text-uppercase font-weight-bold"
          >
            {{ item.bot_status }}
          </v-chip>
        </template>

        <!-- Actions -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex justify-end gap-1">
            <!-- 1. Run Bot -->
            <v-tooltip text="Run Auto-Download" location="top">
              <template v-slot:activator="{ props }">
                <v-btn 
                  v-bind="props"
                  icon="mdi-robot" 
                  size="small" 
                  variant="text" 
                  color="orange-darken-2" 
                  @click="runBot(item)"
                  :loading="item.bot_status === 'running'"
                  :disabled="item.bot_status === 'running'"
                ></v-btn>
              </template>
            </v-tooltip>

            <!-- 2. Download Result ZIP -->
            <v-tooltip text="Download Invoices (ZIP)" location="top" v-if="item.generated_zip">
              <template v-slot:activator="{ props }">
                <v-btn 
                  v-bind="props"
                  icon="mdi-folder-zip" 
                  size="small" 
                  variant="text" 
                  color="success"
                  :href="item.generated_zip" 
                  target="_blank"
                ></v-btn>
              </template>
            </v-tooltip>

            <!-- 3. View Details -->
            <v-tooltip text="View Data" location="top">
              <template v-slot:activator="{ props }">
                <v-btn 
                  v-bind="props"
                  icon="mdi-eye" 
                  size="small" 
                  variant="text" 
                  color="info" 
                  @click="viewDetails(item)"
                ></v-btn>
              </template>
            </v-tooltip>

            <!-- 4. Delete -->
            <v-tooltip text="Delete Record" location="top">
              <template v-slot:activator="{ props }">
                <v-btn 
                  v-bind="props"
                  icon="mdi-delete" 
                  size="small" 
                  variant="text" 
                  color="error" 
                  @click="deleteItem(item)"
                ></v-btn>
              </template>
            </v-tooltip>
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <!-- Dialogs (Upload, Details, Delete) -->
    <v-dialog v-model="dialogUpload" max-width="500px">
      <ImportForm @close="dialogUpload = false" @saved="onUploaded" />
    </v-dialog>

    <!-- DETAILS DIALOG (Updated with Filters) -->
    <v-dialog v-model="dialogDetails" fullscreen transition="dialog-bottom-transition" scrollable>
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-btn icon @click="dialogDetails = false"><v-icon>mdi-close</v-icon></v-btn>
          <v-toolbar-title class="font-weight-medium">
            Details: {{ selectedImport ? getFileName(selectedImport.file) : '' }}
          </v-toolbar-title>
          <v-spacer></v-spacer>
        </v-toolbar>
        
        <v-card-text class="bg-grey-lighten-5 pa-4">
            <v-card class="rounded-lg elevation-1">
              <v-card-text>
                <!-- Filters Toolbar -->
                <v-row class="mb-2" align="center" dense>
                    <v-col cols="12" sm="3">
                        <v-autocomplete
                            v-model="selectedForwarder"
                            :items="forwarderList"
                            item-title="name"
                            item-value="name" 
                            label="Filter by Forwarder"
                            density="compact"
                            variant="outlined"
                            clearable
                            hide-details
                            bg-color="white"
                            prepend-inner-icon="mdi-filter"
                        ></v-autocomplete>
                    </v-col>
                    <v-col cols="12" sm="3">
                        <v-autocomplete
                            v-model="selectedDestination"
                            :items="destinationList"
                            item-title="name"
                            item-value="name" 
                            label="Filter by Destination"
                            density="compact"
                            variant="outlined"
                            clearable
                            hide-details
                            bg-color="white"
                            prepend-inner-icon="mdi-map-marker"
                        ></v-autocomplete>
                    </v-col>
                    <v-col cols="12" sm="6" class="d-flex align-center justify-end" style="gap: 8px">
                        <v-btn color="primary" variant="elevated" @click="applyFilters" prepend-icon="mdi-check" height="40">Apply</v-btn>
                        <v-btn color="grey-darken-1" variant="text" @click="resetFilters" prepend-icon="mdi-refresh" height="40">Reset</v-btn>
                        <span class="text-caption text-grey ml-4 hidden-xs">
                            Showing {{ displayedDetails.length }} records
                        </span>
                    </v-col>
                </v-row>

                <v-divider class="my-3"></v-divider>

                <v-data-table 
                    v-if="selectedImport?.parsed_data" 
                    :items="displayedDetails" 
                    :headers="detailHeaders"
                    density="compact"
                    :items-per-page="20"
                    hover
                    class="elevation-0"
                >
                    <!-- Custom Row Index Column -->
                    <template v-slot:item.index="{ index }">
                        <span class="text-grey">{{ index + 1 }}</span>
                    </template>

                    <!-- Status inside details -->
                    <template v-slot:item.status="{ item }">
                        <v-chip size="x-small" :color="getDetailStatusColor(item.status)" label>{{ item.status }}</v-chip>
                    </template>
                </v-data-table>
              </v-card-text>
            </v-card>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dialogDelete" max-width="400px">
      <v-card>
        <v-card-title class="text-h6 pt-4 px-4">Confirm Deletion</v-card-title>
        <v-card-text class="px-4 pb-0 text-grey-darken-1">
          Are you sure you want to delete this record? This action cannot be undone.
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="dialogDelete = false">Cancel</v-btn>
          <v-btn color="error" variant="elevated" @click="deleteItemConfirm">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" location="bottom right">{{ snackbar.text }}</v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import api, { socket } from '@/api'; 
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

// Date Filters
const selectedPeriod = ref(''); 
const startDate = ref('');
const endDate = ref('');

// Detail Filter State
const forwarderList = ref([]); 
const destinationList = ref([]); 
const selectedForwarder = ref(null); 
const selectedDestination = ref(null); 
const displayedDetails = ref([]); // Store filtered results here

const headers = [
  { title: 'ID', key: 'id', sortable: true, width: '80px' },
  { title: 'File Name', key: 'file', sortable: true },
  { title: 'Uploaded At', key: 'uploaded_at', sortable: true, width: '180px' },
  // { title: 'Status', key: 'bot_status', sortable: true, width: '120px' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end', width: '200px' },
];

const detailHeaders = [
  { title: '#', key: 'index', sortable: false, width: '50px' }, 
  { title: 'Inv #', key: 'invoice_number' },
  { title: 'Customer', key: 'customer' },
  { title: 'Destination', key: 'destination' },
  { title: 'Forwarder', key: 'forwarder' },
  { title: 'Status', key: 'status' },
];

// Apply Logic
const applyFilters = () => {
    if (!selectedImport.value || !selectedImport.value.parsed_data) {
        displayedDetails.value = [];
        return;
    }
    
    let data = selectedImport.value.parsed_data;
    
    if (selectedForwarder.value) {
        data = data.filter(item => 
            item.forwarder && item.forwarder.toUpperCase() === selectedForwarder.value.toUpperCase()
        );
    }
    if (selectedDestination.value) {
        data = data.filter(item => 
            item.destination && item.destination.toUpperCase() === selectedDestination.value.toUpperCase()
        );
    }
    
    displayedDetails.value = data;
};

const resetFilters = () => {
    selectedForwarder.value = null;
    selectedDestination.value = null;
    if (selectedImport.value) {
        displayedDetails.value = selectedImport.value.parsed_data || [];
    }
};

// Load Filter Data (Forwarders & Destinations)
const loadFilters = async () => {
    try {
        const [fRes, dRes] = await Promise.all([
            api.get('forwarders/', { params: { page_size: 100, status: 'Active' } }),
            api.get('destinations/', { params: { page_size: 100, status: 'Active' } })
        ]);
        forwarderList.value = fRes.data.results; 
        destinationList.value = dRes.data.results;
    } catch (e) {
        console.error("Failed to load filters", e);
    }
};

const onPeriodChange = () => {
    if (selectedPeriod.value !== 'custom') {
        refreshData();
    }
};

const getQueryParams = () => {
    const params = {
        period: selectedPeriod.value,
        search: search.value
    };
    if (selectedPeriod.value === 'custom') {
        if (startDate.value) params.start_date = startDate.value;
        if (endDate.value) params.end_date = endDate.value;
    }
    return params;
};

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
    const params = { 
        page: p, 
        page_size: s, 
        ordering: ordering,
        ...getQueryParams() // Add date filters
    };

    const response = await api.get('orders/', { params });
    serverItems.value = response.data.results;
    totalItems.value = response.data.count;
  } catch (error) { 
    console.error(error); 
    showToast('Failed to load data', 'error');
  }
  finally { loading.value = false; }
};

const refreshData = () => {
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
};

const runBot = async (item) => {
  try {
    item.bot_status = 'running'; 
    await api.post(`orders/${item.id}/run_bot/`);
    showToast('Auto-download started in background', 'info');
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

const getDetailStatusColor = (status) => {
    if (status === 'completed') return 'green';
    if (status === 'failed') return 'red';
    if (status === 'processing') return 'orange';
    return 'grey';
};

const onUploaded = () => { dialogUpload.value = false; loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); showToast('File processed!'); };

const viewDetails = (item) => { 
    selectedImport.value = item; 
    selectedForwarder.value = null; 
    selectedDestination.value = null; 
    // Initial display is full list
    displayedDetails.value = item.parsed_data || []; 
    dialogDetails.value = true; 
};

const deleteItem = (item) => { deletedItem.value = item; dialogDelete.value = true; };
const deleteItemConfirm = async () => { await api.delete(`orders/${deletedItem.value.id}/`); loadItems({ page: 1, itemsPerPage: itemsPerPage.value }); dialogDelete.value = false; };
const getFileName = (path) => path ? path.split('/').pop() : '';
const showToast = (text, color = 'success') => { snackbar.value = { show: true, text, color }; };

// --- SOCKET.IO INTEGRATION ---
onMounted(() => {
  loadFilters(); 
  if (!socket.connected) socket.connect();

  socket.on('order_update', (data) => {
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
  });

  socket.on('bot_update', (data) => {
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
    // If viewing details of the active order, update them live too!
    if (selectedImport.value && selectedImport.value.id === data.order_id) {
         // Reload details isn't trivial since we need to fetch fresh data for just that item
         // A simple workaround is reload the list, then find the item in the new list and update selectedImport
         // Or just let the user close/reopen.
    }
  });
});

onUnmounted(() => {
  socket.off('order_update');
  socket.off('bot_update');
});
</script>