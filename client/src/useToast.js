import { reactive } from 'vue';

// Global state shared across the app
const toastState = reactive({
  show: false,
  message: '',
  color: 'success', // success, error, info, warning
});

export function useToast() {
  // Function to trigger the toast
  const showToast = (message, type = 'success') => {
    toastState.message = message;
    
    // Map simple types to Vuetify colors if needed
    if (type === 'error') toastState.color = 'red';
    else if (type === 'warning') toastState.color = 'orange';
    else toastState.color = 'success'; // Green

    toastState.show = true;
  };

  return {
    toastState,
    showToast,
  };
}