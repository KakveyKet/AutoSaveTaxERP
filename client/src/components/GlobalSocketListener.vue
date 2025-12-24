<template>
  <!-- This component has no UI, it just listens for events -->
  <div style="display: none;"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { socket } from '@/api';

onMounted(() => {
  if (!socket.connected) {
    socket.connect();
  }

  // Listen for global events regardless of the current route
  socket.on('bot_update', handleGlobalUpdate);
});

onUnmounted(() => {
  socket.off('bot_update', handleGlobalUpdate);
});

const handleGlobalUpdate = (data) => {
  // Check specifically for the "Batch/File Completed" event
  if (data.type === 'status_change' && data.status === 'completed') {
    
    // Use filename from server data if available, otherwise fall back to ID
    const fileName = data.file_name || `Import #${data.order_id}`;
    
    // Global Alert
    alert(`Download finished for file: ${fileName}`);
  }
};
</script>