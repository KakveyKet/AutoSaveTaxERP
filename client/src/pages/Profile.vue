<template>
  <v-container fluid>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card>
          <v-toolbar color="primary">
            <v-toolbar-title>My Profile</v-toolbar-title>
          </v-toolbar>

          <v-card-text class="mt-4">
            <div class="d-flex flex-column align-center mb-6">
              <v-avatar size="100" color="grey-lighten-2">
                <v-img 
                  v-if="user.profile_picture" 
                  :src="user.profile_picture" 
                  alt="Avatar"
                ></v-img>
                <span v-else class="text-h4 font-weight-bold primary--text">
                  {{ getInitials(user.username) }}
                </span>
              </v-avatar>
              <div class="text-subtitle-1 mt-2 font-weight-bold">{{ user.role.toUpperCase() }}</div>
            </div>

            <v-form @submit.prevent="saveProfile" ref="form">
              <v-text-field
                v-model="user.username"
                label="Username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                :rules="[v => !!v || 'Username is required']"
              ></v-text-field>

              <v-text-field
                v-model="user.email"
                label="Email"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                :rules="[v => !!v || 'Email is required', v => /.+@.+\..+/.test(v) || 'Invalid email']"
              ></v-text-field>

              <v-divider class="my-4"></v-divider>
              <div class="text-subtitle-2 mb-2 text-medium-emphasis">Change Password (Optional)</div>

              <v-text-field
                v-model="user.password"
                label="New Password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                type="password"
                hint="Leave blank to keep current password"
                persistent-hint
              ></v-text-field>
            </v-form>
          </v-card-text>

          <v-card-actions class="pa-4">
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="saveProfile" :loading="loading" min-width="120">
              Save Changes
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Toast Notification -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      location="top"
      timeout="3000"
    >
      {{ snackbar.text }}
      <template v-slot:actions="{ isActive }">
        <v-btn variant="text" @click="isActive.value = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';

// State
const loading = ref(false);
const user = ref({
  id: null,
  username: '',
  email: '',
  role: '',
  profile_picture: null,
  password: '' // Only for updates
});

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
});

// Helper: Decode JWT to find current User ID
const parseJwt = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
};

const getInitials = (name) => {
  return name ? name.substring(0, 2).toUpperCase() : '??';
};

const showToast = (message, color = 'success') => {
  snackbar.value = { show: true, text: message, color: color };
};

// Fetch Data
const fetchProfile = async () => {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  const payload = parseJwt(token);
  if (payload && payload.user_id) {
    loading.value = true;
    try {
      const response = await api.get(`users/${payload.user_id}/`);
      // We don't populate password from backend for security
      user.value = { ...response.data, password: '' };
    } catch (error) {
      console.error('Error fetching profile:', error);
      showToast('Failed to load profile', 'error');
    } finally {
      loading.value = false;
    }
  }
};

// Update Data
const saveProfile = async () => {
  loading.value = true;
  try {
    const payload = { ...user.value };
    
    // Remove password if empty (so we don't overwrite it with blank)
    if (!payload.password) delete payload.password;
    
    // Remove read-only fields that shouldn't be sent back
    delete payload.profile_picture; 
    delete payload.created_at;

    await api.put(`users/${user.value.id}/`, payload);
    
    showToast('Profile updated successfully!', 'success');
    
    // Optional: If password changed, you might want to force logout
    if (payload.password) {
      // localStorage.clear();
      // window.location.reload();
    }
  } catch (error) {
    console.error('Error updating profile:', error);
    showToast('Failed to update profile', 'error');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchProfile();
});
</script>