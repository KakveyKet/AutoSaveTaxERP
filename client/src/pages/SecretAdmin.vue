<template>
  <v-container fluid class="fill-height bg-grey-lighten-4">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="red-darken-3" dark flat>
            <v-toolbar-title>Admin Recovery (Restricted)</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-icon>mdi-shield-lock</v-icon>
          </v-toolbar>

          <v-card-text>
            <v-alert type="warning" variant="tonal" class="mb-4">
               Use this form to reset your password or create an emergency admin account. Requires Master Key.
            </v-alert>

            <v-form @submit.prevent="handleRecovery">
              <!-- Master Key -->
              <v-text-field
                v-model="secretKey"
                label="Master Secret Key"
                prepend-inner-icon="mdi-key-variant"
                variant="outlined"
                type="password"
                :rules="[v => !!v || 'Key is required']"
              ></v-text-field>

              <v-divider class="my-3"></v-divider>

              <!-- New Credentials -->
              <v-text-field
                v-model="username"
                label="Username (Existing or New)"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                :rules="[v => !!v || 'Username is required']"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="New Password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                type="password"
                :rules="[v => !!v || 'Password is required']"
              ></v-text-field>
            </v-form>
          </v-card-text>

          <v-card-actions class="pa-4">
             <v-btn variant="text" to="/login">Back to Login</v-btn>
             <v-spacer></v-spacer>
             <v-btn 
               color="red-darken-3" 
               variant="elevated" 
               @click="handleRecovery" 
               :loading="loading"
             >
               Execute Recovery
             </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
       {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
// We use raw axios to avoid any interceptors since this is public
import axios from 'axios'; 

const router = useRouter();
const secretKey = ref('');
const username = ref('');
const password = ref('');
const loading = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });

// IMPORTANT: Hardcode API URL since we bypass api.js helper
const API_URL = 'http://127.0.0.1:8000/api/secret-recovery/';

const handleRecovery = async () => {
    if(!secretKey.value || !username.value || !password.value) return;

    loading.value = true;
    try {
        await axios.post(API_URL, {
            secret_key: secretKey.value,
            username: username.value,
            password: password.value
        });
        
        snackbar.value = { show: true, text: 'Success! Redirecting to login...', color: 'success' };
        
        setTimeout(() => {
            router.push('/login');
        }, 2000);

    } catch (error) {
        const msg = error.response?.data?.error || 'Recovery Failed. Check Secret Key.';
        snackbar.value = { show: true, text: msg, color: 'error' };
    } finally {
        loading.value = false;
    }
};
</script>