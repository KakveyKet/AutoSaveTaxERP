<template>
  <v-container fluid>
    <v-card class="mb-4">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title>Invoice Download Report</v-toolbar-title>
        <v-spacer></v-spacer>
        
        <v-chip size="x-small" :color="socketConnected ? 'success' : 'error'" class="mr-4" variant="flat">
          <v-icon start size="12">{{ socketConnected ? 'mdi-wifi' : 'mdi-wifi-off' }}</v-icon>
          {{ socketConnected ? 'Live Connection' : 'Disconnected' }}
        </v-chip>
        
        <v-icon class="mr-4">mdi-file-chart</v-icon>
      </v-toolbar>

      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-autocomplete
              v-model="selectedFile"
              :items="fileList"
              item-title="file_name"
              item-value="id"
              label="Select Import File to View Report"
              prepend-inner-icon="mdi-file-excel"
              variant="outlined"
              return-object
              hide-details
              @update:model-value="loadReportData"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :subtitle="new Date(item.raw.uploaded_at).toLocaleString()"></v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
          
          <v-col cols="12" md="6" class="d-flex justify-end">
            <v-btn color="info" variant="tonal" prepend-icon="mdi-refresh" @click="loadReportData" :disabled="!selectedFile || loading" :loading="loading">
              Refresh Report
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Report Content -->
    <v-expand-transition>
      <div v-if="selectedFile && reportData">
        <!-- Summary Cards -->
        <v-row class="mb-2">
          <v-col cols="12" sm="4">
            <v-card color="blue-lighten-5" border elevation="0">
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Total Invoices</div>
                <div class="text-h4 font-weight-bold text-primary">{{ stats.total }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card color="green-lighten-5" border elevation="0">
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Completed</div>
                <div class="text-h4 font-weight-bold text-success">{{ stats.completed }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card color="red-lighten-5" border elevation="0">
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Failed / Pending</div>
                <div class="text-h4 font-weight-bold text-error">{{ stats.failed }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Detailed Table -->
        <v-card title="Invoice Details" class="mt-4">
          <template v-slot:append>
            <v-text-field v-model="search" density="compact" label="Search Invoice" prepend-inner-icon="mdi-magnify" single-line hide-details style="width: 250px" variant="outlined"></v-text-field>
          </template>

          <v-data-table :headers="headers" :items="reportData" :search="search" density="compact" class="elevation-0" :loading="loading">
            <template v-slot:item.status="{ item }">
              <v-chip :color="getStatusColor(item.status)" size="small" class="text-uppercase font-weight-bold" label>
                <v-icon start size="small" :class="item.status === 'processing' ? 'mdi-spin' : ''">{{ getStatusIcon(item.status) }}</v-icon>
                {{ item.status || 'Pending' }}
              </v-chip>
            </template>
            <template v-slot:item.amount="{ item }">
              ${{ Number(item.amount).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon="mdi-file-eye-outline" variant="text" color="primary" size="small" :disabled="item.status !== 'completed'" @click="previewInvoice(item)">
                <v-tooltip activator="parent" location="top">Preview Invoice</v-tooltip>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </div>
    </v-expand-transition>
    
    <v-alert v-if="!selectedFile" type="info" variant="tonal" class="mt-4">
      Please select a file from the dropdown to monitor download progress.
    </v-alert>

    <v-snackbar v-model="notification.show" :color="notification.color" :timeout="4000" location="top right" elevation="10">
      <div class="d-flex align-center">
        <v-icon start size="28">{{ notification.icon }}</v-icon>
        <div class="ml-2">
          <div class="text-subtitle-2 font-weight-bold">{{ notification.title }}</div>
          <div class="text-caption">{{ notification.message }}</div>
        </div>
      </div>
      <template v-slot:actions>
        <v-btn icon="mdi-close" variant="text" @click="notification.show = false"></v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, reactive } from 'vue';
import api, { socket } from '@/api';

const fileList = ref([]);
const selectedFile = ref(null);
const reportData = ref([]);
const search = ref('');
const loading = ref(false);
const socketConnected = ref(false);

const notification = reactive({
  show: false, title: '', message: '', color: 'success', icon: 'mdi-check-circle'
});

const headers = [
  { title: 'Invoice #', key: 'invoice_number', align: 'start' },
  { title: 'Customer', key: 'customer' },
  { title: 'Forwarder', key: 'forwarder' },
  { title: 'Status', key: 'status', align: 'center' },
  { title: 'Amount (USD)', key: 'amount', align: 'end' },
  { title: 'Actions', key: 'actions', align: 'center', sortable: false },
];

const stats = computed(() => {
  if (!reportData.value) return { total: 0, completed: 0, failed: 0 };
  const total = reportData.value.length;
  const completed = reportData.value.filter(i => i.status === 'completed').length;
  const failed = reportData.value.filter(i => i.status === 'failed').length;
  return { total, completed, failed: total - completed };
});

// --- PAGE SPECIFIC SOCKET LOGIC ---

// 1. We name this function to handle updates for THIS PAGE ONLY
const handlePageUpdate = (data) => {
  if (selectedFile.value && data.order_id === selectedFile.value.id) {
    // Only update Table rows
    if (data.type === 'progress') {
      const itemIndex = data.index;
      if (reportData.value[itemIndex]) {
        reportData.value[itemIndex].status = data.status;
        if (data.status === 'completed') {
          showNotify("Downloaded", `Invoice ${data.invoice} ready.`, "success", "mdi-check-circle");
        } else if (data.status === 'failed') {
          showNotify("Failed", `Invoice ${data.invoice} failed.`, "error", "mdi-alert-circle");
        }
      }
    }
    // WE DO NOT ALERT HERE (App.vue does it)
  }
};

const setupSocketListeners = () => {
  if (!socket.connected) socket.connect();
  socketConnected.value = socket.connected;

  socket.on('connect', () => { socketConnected.value = true; });
  socket.on('disconnect', () => { socketConnected.value = false; });

  // 2. Add the page-specific listener
  socket.on('bot_update', handlePageUpdate);
};

onMounted(() => {
  setupSocketListeners();
  fetchFiles();
});

onUnmounted(() => {
  socket.off('connect');
  socket.off('disconnect');
  
  // 3. CRITICAL: Remove ONLY the local listener
  // If you use socket.off('bot_update') without arguments, it kills the alert in App.vue!
  socket.off('bot_update', handlePageUpdate);
});

const fetchFiles = async () => {
  try {
    const response = await api.get('orders/', { params: { page_size: 50 } });
    fileList.value = response.data.results.map(f => ({
      ...f,
      file_name: f.file ? f.file.split('/').pop() : `Import #${f.id}`
    }));
  } catch (e) {
    console.error("Failed to fetch order history", e);
  }
};

const loadReportData = async () => {
  if (!selectedFile.value) return;
  loading.value = true;
  try {
    const response = await api.get(`orders/${selectedFile.value.id}/`);
    reportData.value = response.data.parsed_data || [];
  } catch (e) {
    showNotify("Error", "Could not load report details", "error", "mdi-alert");
  } finally {
    loading.value = false;
  }
};

const previewInvoice = (item) => {
  const url = `${api.defaults.baseURL}orders/${selectedFile.value.id}/preview/${item.invoice_number}/`;
  window.open(url, '_blank');
};

const showNotify = (title, message, color = 'success', icon = 'mdi-check-circle') => {
  notification.title = title;
  notification.message = message;
  notification.color = color;
  notification.icon = icon;
  notification.show = true;
};

const getStatusColor = (status) => {
  const colors = { 'completed': 'success', 'processing': 'info', 'downloading': 'info', 'failed': 'error', 'pending': 'grey' };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = { 'completed': 'mdi-check-circle', 'processing': 'mdi-loading mdi-spin', 'downloading': 'mdi-loading mdi-spin', 'failed': 'mdi-alert-circle', 'pending': 'mdi-clock-outline' };
  return icons[status] || 'mdi-help-circle-outline';
};
</script>