import { reactive } from 'vue';

// The reactive state object that drives the UI
export const notification = reactive({
  show: false,
  color: 'info',
  icon: 'mdi-information',
  title: '',
  message: '',
});

// The helper methods you call from your components
export const toast = {
  show(title, message, color = 'info', icon = 'mdi-information') {
    notification.title = title;
    notification.message = message;
    notification.color = color;
    notification.icon = icon;
    notification.show = true;
  },
  
  success(message, title = 'Success') {
    this.show(title, message, 'success', 'mdi-check-circle');
  },
  
  error(message, title = 'Error') {
    this.show(title, message, 'error', 'mdi-alert-circle');
  },
  
  info(message, title = 'Info') {
    this.show(title, message, 'info', 'mdi-information');
  },
  
  warning(message, title = 'Warning') {
    this.show(title, message, 'warning', 'mdi-alert');
  },

  // Specific helper for downloads if you want custom styling
  downloadComplete(fileName) {
    this.show('Download Complete', `${fileName} has been downloaded successfully.`, 'success', 'mdi-download-check');
  }
};