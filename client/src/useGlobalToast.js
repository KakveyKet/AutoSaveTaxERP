import { ref } from 'vue';

// Global state must be outside the function to be shared across the app
const show = ref(false);
const message = ref('');
const color = ref('success');
const timeout = ref(5000);

export function useGlobalToast() {
  
  const showToast = (msg, type = 'success', time = 5000) => {
    console.log("Toast Triggered:", msg); // Debug log
    message.value = msg;
    color.value = type; // 'success', 'error', 'info', 'warning'
    timeout.value = time;
    show.value = true;
  };

  return {
    show,
    message,
    color,
    timeout,
    showToast
  };
}