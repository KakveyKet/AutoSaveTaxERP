import { reactive } from 'vue';
import api, { socket } from '@/api';
import { toast } from '@/store/useToast';

// --- STATE ---
const state = reactive({
  isInitialized: false,
  socketConnected: false,
  // You can add other global bot states here if needed (e.g. isRunning)
});

// --- ACTIONS ---
const actions = {
  initialize() {
    // Prevent double initialization
    if (state.isInitialized) return;

    if (!socket.connected) {
        socket.connect();
    }

    // Connection Listeners
    socket.on('connect', () => {
      state.socketConnected = true;
      console.log("[BotStore] Socket Connected");
    });

    socket.on('disconnect', () => {
      state.socketConnected = false;
      console.log("[BotStore] Socket Disconnected");
    });

    // --- GLOBAL BOT LISTENER ---
    // This is the SINGLE source of truth for global notifications
    socket.on('bot_update', (data) => {
      console.log("[BotStore] Received Update:", data);

      // 1. Success/Fail for individual invoices
      if (data.type === 'progress') {
        if (data.status === 'completed') {
          toast.success(`Invoice ${data.invoice} captured successfully.`, "Download Success");
        } else if (data.status === 'failed') {
          toast.error(`Failed to capture invoice ${data.invoice}.`, "Process Failed");
        }
      }

      // 2. Batch Completion
      if (data.type === 'status_change' && data.status === 'completed') {
        toast.info(data.message, "Batch Finished");
      }
    });

    state.isInitialized = true;
  },

  // Call this if you ever need to forcefully stop listening (e.g. Logout)
  cleanup() {
    socket.off('connect');
    socket.off('disconnect');
    socket.off('bot_update');
    state.isInitialized = false;
    state.socketConnected = false;
  }
};

// Export as a composable
export const useBotSocket = () => {
  return {
    state,
    ...actions
  };
};