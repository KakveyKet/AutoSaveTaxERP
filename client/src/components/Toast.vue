<template>
  <v-snackbar
    v-model="toastState.show"
    :color="toastState.color"
    location="top right"
    timeout="3000"
    elevation="4"
  >
    <div class="d-flex align-center">
      <v-icon icon="mdi-bell-ring" class="me-2"></v-icon>
      {{ toastState.message }}
    </div>

    <template v-slot:actions>
      <v-btn
        icon="mdi-close"
        variant="text"
        size="small"
        @click="toastState.show = false"
      ></v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { useToast } from '@/composables/useToast';

// Connect to the global state
const { toastState } = useToast();
</script>