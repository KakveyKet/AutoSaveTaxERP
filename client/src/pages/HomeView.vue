<template>
  <v-container fluid>
    <h1 class="text-h4 font-weight-bold mb-4 text-grey-darken-3">Dashboard</h1>

    <!-- 1. Stats Row -->
    <v-row>
      <!-- ... (No changes to stats cards) ... -->
      <v-col cols="12" sm="6" md="3">
        <v-card color="primary" class="text-white" elevation="2">
          <v-card-text>
            <div class="text-overline mb-1">Total Users</div>
            <div class="text-h4 font-weight-bold">{{ stats.total_users }}</div>
            <v-icon size="64" class="position-absolute" style="right: -10px; bottom: -10px; opacity: 0.3;">mdi-account-group</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="info" class="text-white" elevation="2">
          <v-card-text>
            <div class="text-overline mb-1">Total Forwarders</div>
            <div class="text-h4 font-weight-bold">{{ stats.total_forwarders }}</div>
            <v-icon size="64" class="position-absolute" style="right: -10px; bottom: -10px; opacity: 0.3;">mdi-truck</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="success" class="text-white" elevation="2">
          <v-card-text>
            <div class="text-overline mb-1">Total Destinations</div>
            <div class="text-h4 font-weight-bold">{{ stats.total_destinations }}</div>
            <v-icon size="64" class="position-absolute" style="right: -10px; bottom: -10px; opacity: 0.3;">mdi-map-marker</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card color="warning" class="text-white" elevation="2">
          <v-card-text>
            <div class="text-overline mb-1">Total Uploads</div>
            <div class="text-h4 font-weight-bold">{{ stats.total_orders }}</div>
            <v-icon size="64" class="position-absolute" style="right: -10px; bottom: -10px; opacity: 0.3;">mdi-file-excel</v-icon>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 2. Main Content: Calendar + Quick Action -->
    <v-row class="mt-4">
      <!-- CALENDAR SECTION -->
      <v-col cols="12" md="8">
        <v-card title="Upload History Calendar" elevation="1">
          <v-card-text>
            <!-- Calendar Toolbar -->
            <v-sheet class="d-flex flex-wrap align-center" tile>
              <v-btn class="ma-2" variant="text" icon @click="$refs.calendar.prev()">
                <v-icon>mdi-chevron-left</v-icon>
              </v-btn>
              
              <v-spacer></v-spacer>
              
              <v-select
                v-model="type"
                :items="types"
                class="ma-2"
                density="compact"
                label="View Type"
                variant="outlined"
                hide-details
                style="max-width: 120px;"
              ></v-select>
              
              <v-btn class="ma-2" variant="text" icon @click="$refs.calendar.next()">
                <v-icon>mdi-chevron-right</v-icon>
              </v-btn>
            </v-sheet>

            <!-- The V-Calendar Component -->
            <v-sheet height="600">
              <v-calendar
                ref="calendar"
                v-model="value"
                :events="events"
                :type="type"
                :weekdays="weekday"
                color="primary"
                @click:event="downloadEventFile"
              >
                <!-- Custom Event Template -->
                <template #event="{ event }">
                    <!-- Dynamic class for color: 'bg-warning' for today, 'bg-primary' for past -->
                    <div 
                        class="calendar-event"
                        :class="isToday(event.start) ? 'bg-warning' : 'bg-primary'"
                    >
                        {{ event.title }}
                    </div>
                </template>
              </v-calendar>
            </v-sheet>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- SIDEBAR: Quick Upload & List -->
      <v-col cols="12" md="4">
        <!-- Quick Upload -->
        <v-card class="mb-4 text-center pa-4" elevation="1" border>
          <v-icon size="48" color="primary" class="mb-2">mdi-cloud-upload</v-icon>
          <h3 class="text-h6">Quick Import</h3>
          <p class="text-caption text-grey mb-4">Upload new shipment checklists instantly.</p>
          <v-btn color="primary" block @click="dialogUpload = true">
            Upload File
          </v-btn>
        </v-card>

        <!-- Recent List -->
        <v-card title="Recent Activity" elevation="1">
          <v-list lines="two" density="compact">
            <v-list-item
              v-for="item in recentUploads"
              :key="item.id"
              :title="getFileName(item.file)"
              :subtitle="formatDate(item.uploaded_at)"
            >
              <template v-slot:prepend>
                <v-avatar color="green-lighten-5" icon="mdi-file-excel" color-text="green"></v-avatar>
              </template>
           
            </v-list-item>
            <v-list-item v-if="recentUploads.length === 0">
              <v-list-item-title class="text-grey font-italic">No uploads yet</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <!-- Upload Popup -->
    <v-dialog v-model="dialogUpload" max-width="500px">
      <ImportForm @close="dialogUpload = false" @saved="onUploaded" />
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { VCalendar } from 'vuetify/components';
import api from '@/api';
import ImportForm from '@/form/ImportForm.vue';

// --- Dashboard State ---
const stats = ref({ total_users: 0, total_forwarders: 0, total_destinations: 0, total_orders: 0 });
const recentUploads = ref([]);
const dialogUpload = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });

// --- Calendar State ---
const type = ref('month');
const types = ['month', 'week', 'day'];
const weekday = ref([0, 1, 2, 3, 4, 5, 6]);
const value = ref([new Date()]);
const events = ref([]);

// --- Actions --- 

const fetchStats = async () => {
  try {
    const response = await api.get('dashboard/stats/');
    stats.value = response.data;
    
    if (response.data.recent_uploads) {
      recentUploads.value = response.data.recent_uploads;
      mapUploadsToEvents(response.data.recent_uploads);
    }
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
  }
};

const mapUploadsToEvents = (uploads) => {
  const todayStr = new Date().toDateString();

  events.value = uploads.map(upload => {
    const uploadDate = new Date(upload.uploaded_at);
    // Determine color based on date: Today = warning (orange), Past = primary (blue)
    const isToday = uploadDate.toDateString() === todayStr;
    const color = isToday ? 'warning' : 'primary';

    // RECOMMENDATION: Include time in title to distinguish multiple daily uploads
    const timeStr = uploadDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return {
      title: `Uploaded ${timeStr}`, 
      file: upload.file, 
      start: uploadDate, 
      end: uploadDate, 
      color: color, 
      allDay: false // Changed to false so they stack by time if using day/week view
    };
  });
};

const downloadEventFile = (data) => {
  const event = data.event || data;
  if (event && event.file) {
    window.open(event.file, '_blank');
  }
};

// Helper to check if a date object is "today"
const isToday = (dateObj) => {
    if (!dateObj) return false;
    const today = new Date();
    return dateObj.getDate() === today.getDate() &&
           dateObj.getMonth() === today.getMonth() &&
           dateObj.getFullYear() === today.getFullYear();
};

const onUploaded = () => {
  dialogUpload.value = false;
  snackbar.value = { show: true, text: 'File uploaded successfully!', color: 'success' };
  fetchStats(); // Refresh data immediately
};

// --- Helpers ---
const getFileName = (path) => {
  if (!path) return 'Unknown File';
  return path.split('/').pop();
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
};

// Init
onMounted(() => {
  fetchStats();
});
</script>

<style scoped>
/* Custom style for the event chip inside the calendar */
.calendar-event {
    color: white; 
    font-size: 12px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    text-align: center;
    width: 100%;
    cursor: pointer;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
</style>