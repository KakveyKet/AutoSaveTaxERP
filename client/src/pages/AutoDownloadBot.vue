<template>
  <v-container fluid>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="elevation-2">
          <v-toolbar color="primary" dark>
            <v-toolbar-title>Auto-Download Bot Runner</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-icon class="mr-4">mdi-robot</v-icon>
          </v-toolbar>

          <v-card-text class="pa-6">
            <!-- 1. Select Order Import -->
            <h3 class="text-h6 mb-2">1. Select Import File</h3>
            <p class="text-caption text-grey mb-4">Choose the uploaded Excel file containing the invoices you want to
              process.</p>

            <v-autocomplete v-model="selectedOrder" :items="orderImports" item-title="file_name" item-value="id"
              label="Select Order Import" variant="outlined" prepend-inner-icon="mdi-file-excel"
              :loading="loadingOrders" return-object clearable>
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :subtitle="formatDate(item.raw.uploaded_at)"></v-list-item>
              </template>
            </v-autocomplete>

            <v-divider class="my-6"></v-divider>


            <!-- 3. Actions -->
            <h3 class="text-h6 mb-4">2. Execute</h3>

            <div class="d-flex flex-column gap-3">
              <!-- LOGIN ONLY BUTTON (Start) -->
              <v-btn v-if="!isRunning" size="large" color="info" variant="outlined" prepend-icon="mdi-login"
                :disabled="!selectedOrder" @click="runBot('login_only')" class="mb-3">
                Start Download
              </v-btn>

              <!-- STOP BOT BUTTON (Only visible when running) -->
              <v-btn v-if="isRunning" size="large" color="error" variant="flat" prepend-icon="mdi-stop" @click="stopBot"
                class="mb-3">
                STOP BOT
              </v-btn>

         
            </div>

            <!-- Status Output -->
            <v-expand-transition>
              <div v-if="statusMessage" class="mt-6">
                <v-alert :type="statusType" border="start" elevation="2" closable>
                  <div class="text-subtitle-1 font-weight-bold mb-1">Bot Status</div>
                  <div>{{ statusMessage }}</div>
                </v-alert>
              </div>
            </v-expand-transition>

          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from '@/api';

// State
const orderImports = ref([]);
const selectedOrder = ref(null);
const loadingOrders = ref(false);
const isRunning = ref(false);
const statusMessage = ref('');
const statusType = ref('info');
const snackbar = ref({ show: false, text: '', color: 'success' });
let statusInterval = null;

// Default settings
const settings = ref({
  target_url: 'Loading...',
  username: 'Loading...',
  headless: false
});

onMounted(() => {
  loadOrderImports();
  loadSettings();
});

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval);
});

const loadSettings = () => {
  const saved = localStorage.getItem('bot_settings');
  if (saved) {
    const parsed = JSON.parse(saved);
    settings.value = {
      target_url: parsed.target_url || 'https://...',
      username: parsed.username || 'Not set',
      headless: parsed.headless || false
    };
  } else {
    settings.value = { target_url: 'Not Configured', username: 'Not Configured', headless: false };
  }
};

const loadOrderImports = async () => {
  loadingOrders.value = true;
  try {
    const response = await api.get('orders/', { params: { page_size: 20 } });
    orderImports.value = response.data.results.map(order => ({
      ...order,
      file_name: order.file.split('/').pop()
    }));

    if (orderImports.value.length > 0) {
      selectedOrder.value = orderImports.value[0];
      // Check if this order is already running
      if (selectedOrder.value.bot_status === 'running') {
        isRunning.value = true;
        statusMessage.value = "Bot is currently running...";
        pollStatus(selectedOrder.value.id);
      }
    }
  } catch (error) {
    console.error('Error loading orders:', error);
    showToast('Failed to load import files', 'error');
  } finally {
    loadingOrders.value = false;
  }
};

const runBot = async (mode) => {
  if (!selectedOrder.value) return;

  isRunning.value = true;
  statusMessage.value = 'Initializing Bot...';
  statusType.value = 'info';

  try {
    const savedSettings = localStorage.getItem('bot_settings');
    const config = savedSettings ? JSON.parse(savedSettings) : {};
    config.mode = mode;

    const response = await api.post(`orders/${selectedOrder.value.id}/run_bot/`, config);

    statusMessage.value = response.data.message || 'Bot started successfully.';
    statusType.value = 'success';
    showToast('Bot process started', 'success');

    pollStatus(selectedOrder.value.id);

  } catch (error) {
    console.error('Bot start error:', error);
    statusMessage.value = error.response?.data?.message || 'Failed to start bot.';
    statusType.value = 'error';
    showToast('Error starting bot', 'error');
    isRunning.value = false;
  }
};

// --- NEW STOP BOT FUNCTION ---
const stopBot = async () => {
  if (!selectedOrder.value) return;

  try {
    await api.post(`orders/${selectedOrder.value.id}/stop_bot/`);
    statusMessage.value = "Stop signal sent. Bot stopping...";
    statusType.value = 'warning';
    showToast('Stop signal sent', 'warning');
    // We keep polling; eventually status becomes 'cancelled' or 'failed'
  } catch (error) {
    console.error('Stop error:', error);
    showToast('Failed to stop bot', 'error');
  }
};

const pollStatus = (orderId) => {
  if (statusInterval) clearInterval(statusInterval);

  statusInterval = setInterval(async () => {
    try {
      const res = await api.get(`orders/${orderId}/`);
      const status = res.data.bot_status;
      const msg = res.data.bot_message;

      if (status === 'running') {
        statusMessage.value = `Bot is running... (${msg || 'Processing'})`;
        isRunning.value = true;
      } else if (status === 'completed') {
        statusMessage.value = `Bot Completed: ${msg}`;
        statusType.value = 'success';
        isRunning.value = false;
        clearInterval(statusInterval);
      } else if (status === 'failed' || status === 'cancelled') {
        statusMessage.value = `Bot Stopped/Failed: ${msg}`;
        statusType.value = 'error';
        isRunning.value = false;
        clearInterval(statusInterval);
      }
    } catch (e) {
      clearInterval(statusInterval);
      isRunning.value = false;
    }
  }, 2000);
};
  
// Helpers
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
};

const showToast = (text, color = 'success') => {
  snackbar.value = { show: true, text, color };
};
</script>