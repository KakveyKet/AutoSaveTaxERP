import { onMounted, onUnmounted } from 'vue';
import { socket } from '@/api'; 

export function useGlobalSocket() {
  
  // This function handles events that should trigger REGARDLESS of the current route
  const handleGlobalBotUpdates = (data) => {
    
    // 1. Handle Batch Completion
    if (data.type === 'status_change' && data.status === 'completed') {
      // The Alert you requested
      // We use data.file_name if the backend sends it, otherwise fall back to ID
      const name = data.file_name || `Import #${data.order_id}`;
      alert(`✅ Download Finished!\n\nFile: ${name} is ready.`);
    }

    // 2. Handle Batch Failure
    if (data.type === 'status_change' && data.status === 'failed') {
      const name = data.file_name || `Import #${data.order_id}`;
      alert(`❌ Download Failed for ${name}`);
    }
  };

  onMounted(() => {
    // 1. Ensure socket is connected globally
    if (!socket.connected) {
      socket.connect();
    }

    // 2. Add the global listener
    socket.on('bot_update', handleGlobalBotUpdates);
  });

  onUnmounted(() => {
    // Clean up ONLY this specific listener function
    // Do NOT call socket.disconnect() here, or you will kill connections for other pages
    socket.off('bot_update', handleGlobalBotUpdates);
  });
}