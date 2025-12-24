<template>
  <v-snackbar
    v-model="notification.show"
    :color="notification.color"
    :timeout="4000"
    location="top right"
    elevation="10"
    class="global-snackbar"
  >
    <div class="d-flex align-center">
      <v-icon start size="28" color="white">{{ notification.icon }}</v-icon>
      <div class="ml-2 text-white">
        <div class="text-subtitle-2 font-weight-bold">{{ notification.title }}</div>
        <div class="text-caption">{{ notification.message }}</div>
      </div>
    </div>
    
    <template v-slot:actions>
      <v-btn 
        icon="mdi-close" 
        variant="text" 
        color="white" 
        @click="notification.show = false"
      ></v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { notification } from '@/store/useToast';
</script>

<style scoped>
/* Optional: Ensure z-index is high enough to sit over dialogs */
.global-snackbar {
  z-index: 9999;
}
</style>