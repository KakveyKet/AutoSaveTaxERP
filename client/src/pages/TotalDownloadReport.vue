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
        <v-row class="mb-2 justify-center">
            <v-col cols="12" class="d-flex flex-column align-center">
                <v-btn-toggle
                    v-model="selectedPeriod"
                    color="primary"
                    variant="outlined"
                    divided
                    mandatory
                    class="mb-4"
                    @update:model-value="onPeriodChange"
                >
                    <v-btn value="">All Time</v-btn>
                    <v-btn value="daily">Today</v-btn>
                    <v-btn value="weekly">This Week</v-btn>
                    <v-btn value="monthly">This Month</v-btn>
                    <v-btn value="custom">Custom Range</v-btn> <!-- NEW -->
                </v-btn-toggle>

                <!-- Custom Date Inputs (Visible only when 'custom' is selected) -->
                <div v-if="selectedPeriod === 'custom'" class="d-flex align-center gap-4" style="gap: 16px">
                    <v-text-field
                        v-model="startDate"
                        label="Start Date"
                        type="date"
                        density="compact"
                        variant="outlined"
                        hide-details
                        style="width: 160px"
                    ></v-text-field>
                    <span class="text-h6">-</span>
                    <v-text-field
                        v-model="endDate"
                        label="End Date"
                        type="date"
                        density="compact"
                        variant="outlined"
                        hide-details
                        style="width: 160px"
                    ></v-text-field>
                    <v-btn color="primary" @click="refreshData" prepend-icon="mdi-filter">Apply</v-btn>
                </div>
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
      </v-data-table-server>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';

const selectedPeriod = ref(''); 
const startDate = ref(''); // NEW
const endDate = ref('');   // NEW
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
];

const onPeriodChange = () => {
    // If user selects "Custom", don't refresh immediately (wait for them to pick dates)
    if (selectedPeriod.value !== 'custom') {
        refreshData();
    }
};

const getQueryParams = () => {
    const params = {
        period: selectedPeriod.value,
        search: search.value
    };
    // Add dates if custom period is selected
    if (selectedPeriod.value === 'custom') {
        if (startDate.value) params.start_date = startDate.value;
        if (endDate.value) params.end_date = endDate.value;
    }
    return params;
};

const loadItems = async ({ page, itemsPerPage } = {}) => {
    loading.value = true;
    // Default pagination if called without arguments
    const p = page || 1;
    const s = itemsPerPage || 10;

    try {
        const params = { 
            page: p, 
            page_size: s, 
            ...getQueryParams()
        };

        const response = await api.get('orders/', { params });
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
        const params = getQueryParams();
        const response = await api.get('orders/report_stats/', { params });
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

onMounted(() => {
    loadStats();
});
</script>