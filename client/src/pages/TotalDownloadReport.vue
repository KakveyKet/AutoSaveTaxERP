<template>
  <v-container fluid>
    <v-card class="mb-4">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title>Total Download File Report</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="refreshData"><v-icon>mdi-refresh</v-icon></v-btn>
      </v-toolbar>

      <v-card-text>
        <!-- Period Filter -->
        <v-row class="mb-2">
            <v-col cols="12" sm="12" class="d-flex justify-center">
                <v-btn-toggle
                    v-model="selectedPeriod"
                    color="primary"
                    variant="outlined"
                    divided
                    mandatory
                    @update:model-value="refreshData"
                >
                    <v-btn value="">All Time</v-btn>
                    <v-btn value="daily">Today</v-btn>
                    <v-btn value="weekly">This Week</v-btn>
                    <v-btn value="monthly">This Month</v-btn>
                </v-btn-toggle>
            </v-col>
        </v-row>

        <!-- Summary Statistics -->
        <v-row>
          <v-col cols="12" sm="6" md="3">
            <v-card color="blue-lighten-5" class="text-center pa-2" border>
              <div class="text-caption font-weight-bold text-uppercase text-medium-emphasis">Files Uploaded</div>
              <div class="text-h4 font-weight-bold text-primary">{{ stats.total_files }}</div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card color="grey-lighten-4" class="text-center pa-2" border>
              <div class="text-caption font-weight-bold text-uppercase text-medium-emphasis">Total Invoices Found</div>
              <div class="text-h4 font-weight-bold">{{ stats.total_invoices }}</div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card color="green-lighten-5" class="text-center pa-2" border>
              <div class="text-caption font-weight-bold text-uppercase text-medium-emphasis">Successfully Downloaded</div>
              <div class="text-h4 font-weight-bold text-success">{{ stats.total_downloaded }}</div>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card color="orange-lighten-5" class="text-center pa-2" border>
              <div class="text-caption font-weight-bold text-uppercase text-medium-emphasis">Success Rate</div>
              <div class="text-h4 font-weight-bold text-orange-darken-2">{{ stats.success_rate }}%</div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>

      <v-divider></v-divider>

      <!-- Main History Table -->
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
        <!-- File Name -->
        <template v-slot:item.file="{ item }">
          <span class="font-weight-medium">{{ getFileName(item.file) }}</span>
        </template>

        <!-- Uploaded At -->
        <template v-slot:item.uploaded_at="{ item }">
          {{ new Date(item.uploaded_at).toLocaleString() }}
        </template>

        <!-- Download Stats Column -->
        <template v-slot:item.download_progress="{ item }">
             <v-progress-linear
                :model-value="getSuccessRate(item)"
                color="success"
                height="20"
                striped
             >
                <template v-slot:default="{ value }">
                    <strong class="text-white" style="font-size: 10px">{{ Math.ceil(value) }}% ({{ getCompletedCount(item) }}/{{ getTotalCount(item) }})</strong>
                </template>
             </v-progress-linear>
        </template>

        <!-- Status -->
        <!-- <template v-slot:item.bot_status="{ item }">
            <v-chip size="x-small" :color="getBotColor(item.bot_status)" label class="text-uppercase font-weight-bold">
                {{ item.bot_status }}
            </v-chip>
        </template> -->
      </v-data-table-server>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import api from '@/api';

const selectedPeriod = ref(''); // Default: All Time
const search = ref('');
const serverItems = ref([]);
const totalItems = ref(0);
const loading = ref(false);
const itemsPerPage = ref(10);
const stats = ref({ total_files: 0, total_invoices: 0, total_downloaded: 0, success_rate: 0 });

const headers = [
    { title: 'Date', key: 'uploaded_at', width: '20%' },
    { title: 'File Name', key: 'file' },
    { title: 'Download Progress', key: 'download_progress', sortable: false, width: '25%' },
    // { title: 'Status', key: 'bot_status', align: 'center', width: '15%' },
];

const loadItems = async ({ page, itemsPerPage }) => {
    loading.value = true;
    try {
        const response = await api.get('orders/', { 
            params: { 
                page, 
                page_size: itemsPerPage, 
                search: search.value,
                period: selectedPeriod.value // Send filter to backend
            } 
        });
        serverItems.value = response.data.results;
        totalItems.value = response.data.count;
    } catch (error) {
        console.error("Error loading table", error);
    } finally {
        loading.value = false;
    }
};

const loadStats = async () => {
    try {
        const response = await api.get('orders/report_stats/', {
            params: { period: selectedPeriod.value }
        });
        stats.value = response.data;
    } catch (error) {
        console.error("Error loading stats", error);
    }
};

const refreshData = () => {
    loadStats();
    loadItems({ page: 1, itemsPerPage: itemsPerPage.value });
};

// --- Helpers ---
const getFileName = (path) => path ? path.split('/').pop() : '';

const getTotalCount = (item) => item.parsed_data ? item.parsed_data.length : 0;

const getCompletedCount = (item) => {
    if (!item.parsed_data) return 0;
    return item.parsed_data.filter(i => i.status === 'completed').length;
};

const getSuccessRate = (item) => {
    const total = getTotalCount(item);
    if (total === 0) return 0;
    return (getCompletedCount(item) / total) * 100;
};

const getBotColor = (status) => {
  switch (status) {
    case 'completed': return 'success';
    case 'running': return 'info';
    case 'failed': return 'error';
    case 'cancelled': return 'warning';
    default: return 'grey';
  }
};

onMounted(() => {
    loadStats();
});
</script>