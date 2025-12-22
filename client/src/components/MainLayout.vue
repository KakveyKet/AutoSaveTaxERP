<template>
  <!-- v-app is required for Vuetify layout components -->
  <v-app>
    <!-- 1. SIDEBAR (Navigation Drawer) -->
    <v-navigation-drawer v-model="drawer" app>
      <v-list>
        <!-- Dynamic User Profile -->
        <v-list-item :prepend-avatar="userAvatar" :title="userData.username || 'User'"
          :subtitle="userData.email || 'Loading...'" to="/profile" link></v-list-item>
      </v-list>

      <v-divider></v-divider>

      <v-list density="compact" nav color="primary">
        <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" to="/dashboard"></v-list-item>

        <!-- Only Admins can see these management items -->
       <!-- Management Section: Visible to Admin OR User -->
        <div v-if="['admin', 'user'].includes(userData.role)">
          <v-list-subheader class="text-uppercase font-weight-bold ml-2 text-caption">Management</v-list-subheader>

          <!-- Visible to both Admin and User -->
          <v-list-item prepend-icon="mdi-truck" title="Forwarders" to="/forwarders"></v-list-item>
          <v-list-item prepend-icon="mdi-map-marker" title="Destinations" to="/destinations"></v-list-item>

          <!-- STRICTLY ADMIN ONLY -->
          <v-list-item v-if="userData.role === 'admin'" prepend-icon="mdi-account-group" title="Users" to="/users"></v-list-item>
        </div>
        
        <v-divider class="my-2"></v-divider>
        <v-list-subheader class="text-uppercase font-weight-bold ml-2 text-caption">Operations</v-list-subheader>
        
        <v-list-item prepend-icon="mdi-cloud-upload" title="Import Orders" to="/import-list"></v-list-item>

        <v-list-item prepend-icon="mdi-robot" title="Auto Download Bot" to="/auto-download-bot"></v-list-item>

        <!-- <v-list-item 
          prepend-icon="mdi-folder-zip" 
          title="Bot Downloads" 
          to="/downloads"
        ></v-list-item> -->

        <v-list-item prepend-icon="mdi-file-chart" title="Invoice Reports" to="/invoice-report"></v-list-item>
        <v-list-item prepend-icon="mdi-chart-bar" title="Total Download Report" to="/total-report"></v-list-item>

      </v-list>
    </v-navigation-drawer>

    <!-- 2. NAVBAR (App Bar) -->
    <v-app-bar color="primary" elevation="1">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>Auto save tax ERP</v-toolbar-title>
      <v-spacer></v-spacer>

      <!-- Logout Button -->
      <v-btn icon @click="handleLogout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- 3. MAIN CONTENT -->
    <v-main class="bg-grey-lighten-3">
      <v-container fluid>
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api'; // Import your API helper

const drawer = ref(true);
const router = useRouter();

// State for the logged-in user
const userData = ref({
  username: '',
  email: '',
  role: '', // Ensure role is initialized
  profile_picture: null
});

// Computed property to handle avatar fallback
const userAvatar = computed(() => {
  if (userData.value.profile_picture) {
    return userData.value.profile_picture;
  }
  return `https://ui-avatars.com/api/?name=${userData.value.username || 'User'}&background=random`;
});

// Helper to decode JWT token to get user_id
const parseJwt = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
};

// Fetch user data on mount
onMounted(async () => {
  const token = localStorage.getItem('access_token');
  if (token) {
    const payload = parseJwt(token);
    if (payload && payload.user_id) {
      try {
        const response = await api.get(`users/${payload.user_id}/`);
        userData.value = response.data;
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
      }
    }
  }
});

const handleLogout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  router.push('/login');
};
</script>