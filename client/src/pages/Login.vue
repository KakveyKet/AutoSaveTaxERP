<template>
  <v-container class="fill-height bg-grey-lighten-4" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        
        <!-- Main Card -->
        <v-card class="elevation-10 rounded-lg pa-4">
          
          <!-- Logo & Header Section -->
          <div class="text-center mb-6 mt-4">
            <v-avatar color="primary" size="64" class="mb-4 elevation-2">
              <v-icon icon="mdi-shield-lock" size="32" color="white"></v-icon>
            </v-avatar>
            <h2 class="text-h4 font-weight-bold text-primary">Welcome Back</h2>
            <div class="text-subtitle-1 text-medium-emphasis">
              Sign in to access your dashboard
            </div>
          </div>

          <v-card-text>
            <v-form @submit.prevent="handleLogin" ref="form">
              
              <!-- Username -->
              <v-text-field
                v-model="username"
                label="Username"
                prepend-inner-icon="mdi-account-outline"
                variant="outlined"
                color="primary"
                class="mb-2"
                :rules="[rules.required]"
                autocomplete="username"
              ></v-text-field>

              <!-- Password -->
              <v-text-field
                v-model="password"
                label="Password"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
                :type="visible ? 'text' : 'password'"
                variant="outlined"
                color="primary"
                class="mb-1"
                :rules="[rules.required]"
                autocomplete="current-password"
                @click:append-inner="visible = !visible"
              ></v-text-field>

              <!-- Forgot Password Link -->
              <div class="d-flex justify-end mb-6">
                <a href="#" class="text-caption text-decoration-none text-primary font-weight-medium">
                  Forgot password?
                </a>
              </div>

              <!-- Error Alert -->
              <v-expand-transition>
                <div v-if="error">
                  <v-alert
                    type="error"
                    variant="tonal"
                    density="compact"
                    class="mb-4"
                    icon="mdi-alert-circle"
                    closable
                    @click:close="error = ''"
                  >
                    {{ error }}
                  </v-alert>
                </div>
              </v-expand-transition>

              <!-- Submit Button -->
              <v-btn 
                block 
                color="primary" 
                size="large" 
                type="submit" 
                :loading="loading" 
                class="text-uppercase font-weight-bold elevation-2"
                height="48"
              >
                Sign In
              </v-btn>

            </v-form>
          </v-card-text>

          <!-- Footer/Copyright -->
          <v-card-actions class="justify-center mt-2 mb-2">
            <span class="text-caption text-grey">
              &copy; {{ new Date().getFullYear() }} AutoSave ERP System
            </span>
          </v-card-actions>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api'; // <--- Use shared API instance

const router = useRouter();

// State
const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);
const visible = ref(false); // Password visibility toggle

// Validation Rules
const rules = {
  required: value => !!value || 'Field is required.',
};

const handleLogin = async () => {
  // Basic client-side validation check
  if (!username.value || !password.value) {
    error.value = "Please fill in all fields.";
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    // Use 'api' instance. BaseURL is already handled in api.js
    const response = await api.post('token/', { 
      username: username.value,
      password: password.value
    });

    // Save tokens
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);
    
    // Save Role (If your backend sends it)
    if (response.data.role) {
        localStorage.setItem('user_role', response.data.role);
    }

    // Force socket reconnect on login (if needed)
    // import { socket } from '@/api';
    // socket.connect();

    router.push('/');
    
  } catch (err) {
    console.error(err);
    if (err.response && err.response.status === 401) {
      error.value = 'Incorrect username or password.';
    } else if (err.code === 'ERR_NETWORK') {
      error.value = 'Unable to connect to server. Is Backend running?';
    } else {
      error.value = 'An unexpected error occurred.';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.fill-height {
  background: #f5f5f5; 
}
</style>