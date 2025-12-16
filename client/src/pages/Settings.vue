<template>
  <v-container fluid>
    <v-card class="mx-auto" max-width="800">
      <v-toolbar color="primary">
        <v-toolbar-title>Bot Configuration</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn prepend-icon="mdi-content-save" variant="elevated" color="white" class="text-primary" @click="saveSettings">
          Save Settings
        </v-btn>
        </v-toolbar>

      <v-card-text class="mt-4">
        <v-form>
          <!-- 1. Behavior Settings -->
          <h3 class="text-h6 mb-2">Behavior</h3>
          <v-divider class="mb-4"></v-divider>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-switch
                v-model="settings.headless"
                color="primary"
                label="Headless Mode"
                hint="Run browser in background (Invisible)"
                persistent-hint
                inset
              ></v-switch>
            </v-col>
            <v-col cols="12" md="6">
              <v-slider
                v-model="settings.wait_time"
                label="Download Wait Time (Seconds)"
                min="2"
                max="30"
                step="1"
                thumb-label="always"
                color="primary"
              ></v-slider>
            </v-col>
          </v-row>

          <!-- 2. Credentials -->
          <h3 class="text-h6 mt-4 mb-2">Target System Credentials</h3>
          <v-divider class="mb-4"></v-divider>

          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="settings.target_url"
                label="Login URL"
                prepend-inner-icon="mdi-web"
                variant="outlined"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.username"
                label="Username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.password"
                label="Password"
                type="password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="2000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const snackbar = ref({ show: false, text: '', color: 'success' });

// Default Settings
const settings = ref({
  headless: false,
  wait_time: 5,
  target_url: 'https://the-internet.herokuapp.com/login',
  username: 'tomsmith',
  password: 'SuperSecretPassword!'
});

// Load from Local Storage on mount
onMounted(() => {
  const saved = localStorage.getItem('bot_settings');
  if (saved) {
    settings.value = { ...settings.value, ...JSON.parse(saved) };
  }
});

// Save to Local Storage
const saveSettings = () => {
  localStorage.setItem('bot_settings', JSON.stringify(settings.value));
  snackbar.value = { show: true, text: 'Settings saved to browser!', color: 'success' };
};
</script>