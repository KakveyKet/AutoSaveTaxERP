<template>
  <v-app>
    <!-- 1. SIDEBAR -->
    <v-navigation-drawer v-model="drawer" app>
      <v-list>
        <v-list-item :prepend-avatar="userAvatar" :title="userData.username || 'User'"
          :subtitle="userData.email || 'Loading...'" to="/profile" link></v-list-item>
      </v-list>
      <v-divider></v-divider>
      <v-list density="compact" nav color="primary">
        <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" to="/dashboard"></v-list-item>
        
        <!-- Management Section -->
        <div v-if="['admin', 'user'].includes(userData.role)">
          <v-list-subheader class="text-uppercase font-weight-bold ml-2 text-caption">Management</v-list-subheader>
          <v-list-item prepend-icon="mdi-truck" title="Forwarders" to="/forwarders"></v-list-item>
          <v-list-item prepend-icon="mdi-map-marker" title="Destinations" to="/destinations"></v-list-item>
          <v-list-item v-if="userData.role === 'admin'" prepend-icon="mdi-account-group" title="Users" to="/users"></v-list-item>
        </div>
        
        <v-divider class="my-2"></v-divider>
        <v-list-subheader class="text-uppercase font-weight-bold ml-2 text-caption">Operations</v-list-subheader>
        <v-list-item prepend-icon="mdi-cloud-upload" title="Import Orders" to="/import-list"></v-list-item>
        <v-list-item prepend-icon="mdi-robot" title="Auto Download Bot" to="/auto-download-bot"></v-list-item>
        <v-list-item prepend-icon="mdi-file-chart" title="Invoice Reports" to="/invoice-report"></v-list-item>
        <v-list-item prepend-icon="mdi-chart-bar" title="Total Download Report" to="/total-report"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- 2. NAVBAR -->
    <v-app-bar color="primary" elevation="1">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>Auto save tax ERP</v-toolbar-title>
      <v-spacer></v-spacer>
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
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api, { socket } from '@/api'; // <--- 1. Import Socket here

const drawer = ref(true);
const router = useRouter();

// --- GLOBAL SOCKET LOGIC START ---

const handleGlobalSocketEvents = (data) => {
  // DEBUG: Log the exact data payload to see why the 'if' condition fails
  console.log('📦 PRE-CHECK bot_update data:', data);

  // Logic: When a file finishes processing
  if (data.type === 'status_change' && data.status === 'completed') {
    console.log('✅ COMPLETION CONDITION MET'); // Debug log to confirm entry
    
    // Improved Name Extraction based on your logs
    let name = data.file_name;
    if (!name && data.file_url) {
      // Extract "test3.zip" from "/media/downloads/zips/test3.zip"
      name = data.file_url.split('/').pop();
    }
    name = name || `Import #${data.order_id}`;
    
    // Using setTimeout to ensure it doesn't block rendering
    setTimeout(() => {
      alert(`✅ Download Finished!\n\nFile: ${name} is ready.`);
    }, 100);
  }

  // Logic: When a file fails
  if (data.type === 'status_change' && data.status === 'failed') {
    console.log('❌ FAILURE CONDITION MET'); // Debug log
    const name = data.file_name || `Import #${data.order_id}`;
    setTimeout(() => {
      alert(`❌ Download Failed for ${name}`);
    }, 100);
  }
};

onMounted(() => {
  console.log('🚀 App Mounted: Initializing Socket...');
  
  const token = localStorage.getItem('access_token');
  
  // 1. FORCE DISCONNECT to ensure we don't have a stale/anonymous connection
  // This is critical because setting socket.auth doesn't affect an already open connection
  if (socket.connected) {
    console.log('Disconnecting stale connection to reset auth...');
    socket.disconnect();
  }

  // 2. Attach Token for Handshake
  if (token) {
    console.log('🔐 Attaching Auth Token to Socket...');
    socket.auth = { token };
  }

  // 3. Connect
  console.log('Connecting socket...');
  socket.connect();

  // Debug connection status
  socket.on('connect', () => {
    console.log('✅ Socket Connected! ID:', socket.id);
  });
  
  socket.on('connect_error', (err) => {
    console.error('❌ Socket Connection Error:', err);
  });

  // 4. ROBUST LISTENER (Updated)
  // Instead of socket.on('bot_update'), we use onAny to catch the event 
  // even if another component accidentally called socket.off('bot_update').
  socket.onAny((eventName, ...args) => {
    console.log(`🔔 Incoming Event: ${eventName}`, args);
    
    if (eventName === 'bot_update') {
      // args[0] is the data object
      handleGlobalSocketEvents(args[0]);
    }
  });
  
  // Fetch User Data
  fetchUserData();
});

onUnmounted(() => {
  // 5. Clean up listener
  console.log('App Unmounting: Cleaning up socket listeners');
  // socket.off('bot_update'); // No longer needed as we use onAny
  socket.offAny(); // Remove the catch-all logger
  socket.off('connect');
  socket.off('connect_error');
});

// --- GLOBAL SOCKET LOGIC END ---

// User Data Logic
const userData = ref({
  username: '',
  email: '',
  role: '',
  profile_picture: null
});

const userAvatar = computed(() => {
  if (userData.value.profile_picture) return userData.value.profile_picture;
  return `https://ui-avatars.com/api/?name=${userData.value.username || 'User'}&background=random`;
});

const parseJwt = (token) => {
  try { return JSON.parse(atob(token.split('.')[1])); } catch (e) { return null; }
};

const fetchUserData = async () => {
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
};

const handleLogout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  router.push('/login');
};
</script>