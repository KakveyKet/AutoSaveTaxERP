<template>
  <v-container fluid>
    <v-card class="mx-auto" max-width="800">
      <v-toolbar color="primary">
        <v-btn icon @click="cancel">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <v-toolbar-title>{{ isEditMode ? 'Edit Destination' : 'Create New Destination' }}</v-toolbar-title>
      </v-toolbar>

      <v-form @submit.prevent="saveItem" ref="form">
        <v-card-text>
          <v-container>
            <v-row>
              <!-- Name Field -->
              <v-col cols="12">
                <v-text-field
                  v-model="item.name"
                  label="Destination Name"
                  variant="outlined"
                  prepend-inner-icon="mdi-map-marker"
                  :rules="[v => !!v || 'Name is required']"
                  required
                ></v-text-field>
              </v-col>

              <!-- Status Field -->
              <v-col cols="12" md="6">
                <v-select
                  v-model="item.status"
                  :items="['Active', 'Inactive']"
                  label="Status"
                  variant="outlined"
                  prepend-inner-icon="mdi-list-status"
                ></v-select>
              </v-col>
            </v-row>
          </v-container>
          
          <!-- Error Message -->
          <v-alert v-if="errorMessage" type="error" class="mb-3" closable>
            {{ errorMessage }}
          </v-alert>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancel">Cancel</v-btn>
          <v-btn color="primary" type="submit" :loading="loading">
            {{ isEditMode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import api from '@/api';

const props = defineProps({
  itemId: { type: [Number, String], default: null }
});

const emit = defineEmits(['close', 'saved']);

// State
const loading = ref(false);
const errorMessage = ref('');
const item = ref({ name: '', status: 'Active' });

const isEditMode = computed(() => !!props.itemId);

// Actions
const fetchItem = async (id) => {
  loading.value = true;
  try {
    const response = await api.get(`destinations/${id}/`);
    item.value = response.data;
  } catch (error) {
    console.error('Error fetching destination:', error);
    errorMessage.value = 'Could not load data.';
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  item.value = { name: '', status: 'Active' };
  errorMessage.value = '';
};

// Watch for changes in itemId prop to load data or reset form
watch(() => props.itemId, (newId) => {
  if (newId) fetchItem(newId);
  else resetForm();
}, { immediate: true });

const saveItem = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    if (isEditMode.value) {
      await api.put(`destinations/${props.itemId}/`, item.value);
    } else {
      await api.post('destinations/', item.value);
    }
    emit('saved');
  } catch (error) {
    console.error('Save error:', error);
    errorMessage.value = 'Failed to save item.';
  } finally {
    loading.value = false;
  }
};

const cancel = () => emit('close');
</script>