<template>
  <v-container fluid>
    <v-card class="mb-4">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title>Invoice Download Report</v-toolbar-title>
        <v-spacer></v-spacer>
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
                <v-list-item 
                    v-bind="props" 
                    :subtitle="new Date(item.raw.uploaded_at).toLocaleString()"
                ></v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
          
          <v-col cols="12" md="6" class="d-flex justify-end">
            <v-btn 
                color="info" 
                variant="tonal" 
                prepend-icon="mdi-refresh" 
                @click="loadReportData"
                :disabled="!selectedFile"
            >
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
            <v-card color="blue-lighten-5" border>
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Total Invoices</div>
                <div class="text-h4 font-weight-bold text-primary">{{ stats.total }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card color="green-lighten-5" border>
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Downloaded</div>
                <div class="text-h4 font-weight-bold text-success">{{ stats.completed }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="4">
            <v-card color="red-lighten-5" border>
              <v-card-text class="text-center">
                <div class="text-caption text-medium-emphasis text-uppercase">Pending / Failed</div>
                <div class="text-h4 font-weight-bold text-error">{{ stats.failed }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Detailed Table -->
        <v-card title="Invoice Details">
            <template v-slot:append>
                <v-text-field
                    v-model="search"
                    density="compact"
                    label="Search Invoice"
                    prepend-inner-icon="mdi-magnify"
                    single-line
                    hide-details
                    style="width: 250px"
                ></v-text-field>
            </template>

            <v-data-table
                :headers="headers"
                :items="reportData"
                :search="search"
                density="compact"
                class="elevation-1"
            >
                <!-- Status Column -->
                <template v-slot:item.status="{ item }">
                    <v-chip
                        :color="getStatusColor(item.status)"
                        size="small"
                        class="text-uppercase font-weight-bold"
                        label
                    >
                        <v-icon start size="small">
                            {{ getStatusIcon(item.status) }}
                        </v-icon>
                        {{ item.status || 'Pending' }}
                    </v-chip>
                </template>

                <!-- Amount Column -->
                <template v-slot:item.amount="{ item }">
                    ${{ Number(item.amount).toLocaleString() }}
                </template>
            </v-data-table>
        </v-card>
      </div>
    </v-expand-transition>
    
    <v-alert v-if="!selectedFile" type="info" variant="tonal" class="mt-4">
        Please select a file above to view the download report.
    </v-alert>

  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/api';

const fileList = ref([]);
const selectedFile = ref(null);
const reportData = ref([]);
const search = ref('');

const headers = [
    { title: 'Invoice #', key: 'invoice_number', align: 'start' },
    { title: 'Customer', key: 'customer' },
    { title: 'Forwarder', key: 'forwarder' },
    { title: 'Status', key: 'status', align: 'center' },
    { title: 'Amount (USD)', key: 'amount', align: 'end' },
];

const stats = computed(() => {
    if (!reportData.value) return { total: 0, completed: 0, failed: 0 };
    const total = reportData.value.length;
    const completed = reportData.value.filter(i => i.status === 'completed').length;
    return {
        total,
        completed,
        failed: total - completed
    };
});

onMounted(async () => {
    try {
        // Fetch last 20 uploads for the dropdown
        const response = await api.get('orders/', { params: { page_size: 50 } });
        fileList.value = response.data.results.map(f => ({
            ...f,
            file_name: f.file.split('/').pop()
        }));
    } catch (e) {
        console.error("Failed to load files", e);
    }
});

const loadReportData = async () => {
    if (!selectedFile.value) return;
    
    try {
        const response = await api.get(`orders/${selectedFile.value.id}/`);
        // The invoices are stored in 'parsed_data' field
        reportData.value = response.data.parsed_data || [];
    } catch (e) {
        console.error("Failed to load report detail", e);
    }
};

const getStatusColor = (status) => {
    if (status === 'completed') return 'success';
    if (status === 'downloading') return 'info';
    if (status === 'failed') return 'error';
    return 'grey';
};

const getStatusIcon = (status) => {
    if (status === 'completed') return 'mdi-check-circle';
    if (status === 'downloading') return 'mdi-loading mdi-spin';
    if (status === 'failed') return 'mdi-alert-circle';
    return 'mdi-clock-outline';
};
</script>