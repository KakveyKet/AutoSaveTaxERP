<template>
  <v-container fluid>
    <v-card class="mx-auto" max-width="800">
      <v-toolbar color="primary">
        <v-btn icon @click="cancel">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <v-toolbar-title>{{ isEditMode ? 'Edit User' : 'Create New User' }}</v-toolbar-title>
      </v-toolbar>

      <v-form @submit.prevent="saveUser" ref="form">
        <v-card-text>
          <v-container>
            <v-row>
              <!-- Username -->
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="user.username"
                  label="Username"
                  variant="outlined"
                  prepend-inner-icon="mdi-account"
                  :rules="[v => !!v || 'Username is required']"
                  required
                ></v-text-field>
              </v-col>

              <!-- Email -->
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="user.email"
                  label="Email"
                  variant="outlined"
                  prepend-inner-icon="mdi-email"
                  :rules="[
                    v => !!v || 'Email is required',
                    v => /.+@.+\..+/.test(v) || 'E-mail must be valid'
                  ]"
                  required
                ></v-text-field>
              </v-col>

              <!-- Password -->
              <v-col cols="12">
                <v-text-field
                  v-model="user.password"
                  label="Password"
                  variant="outlined"
                  type="password"
                  prepend-inner-icon="mdi-lock"
                  :hint="isEditMode ? 'Leave blank to keep current password' : 'Required for new users'"
                  persistent-hint
                  :rules="passwordRules"
                ></v-text-field>
              </v-col>

              <!-- Role -->
              <v-col cols="12" md="6">
                <v-select
                  v-model="user.role"
                  :items="['admin', 'user', 'guest']"
                  label="Role"
                  variant="outlined"
                  prepend-inner-icon="mdi-badge-account"
                ></v-select>
              </v-col>

              <!-- Status -->
              <v-col cols="12" md="6" class="d-flex align-center">
                <v-switch
                  v-model="user.status"
                  color="success"
                  label="Active Account"
                  inset
                  hide-details
                ></v-switch>
              </v-col>
            </v-row>
          </v-container>
          
          <!-- Error Alert -->
          <v-alert v-if="errorMessage" type="error" class="mb-3" closable>
            {{ errorMessage }}
          </v-alert>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancel">Cancel</v-btn>
          <v-btn color="primary" type="submit" :loading="loading">
            {{ isEditMode ? 'Update User' : 'Create User' }}
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import api from '@/api';
// --- Props & Emits ---
const props = defineProps({
  userId: {
    type: [Number, String],
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

// --- State ---
const loading = ref(false);
const errorMessage = ref('');
const user = ref({
  username: '',
  email: '',
  password: '',
  role: 'user',
  status: true
});

// Computed properties
const isEditMode = computed(() => !!props.userId);

// Validation Rules
const passwordRules = computed(() => {
  if (!isEditMode.value) {
    return [v => !!v || 'Password is required'];
  }
  return []; // Optional in edit mode
});

const fetchUser = async (id) => {
  loading.value = true;

  try {
    const response = await api.get(`users/${id}/`);

    // Fill form (keep password empty)
    user.value = {
      ...response.data,
      password: '',
    };
  } catch (error) {
    console.error('Error fetching user:', error);
    errorMessage.value = 'Could not load user data.';
  } finally {
    loading.value = false;
  }
};

const resetForm = () => {
  user.value = { username: '', email: '', password: '', role: 'user', status: true };
  errorMessage.value = '';
};

// Watch for prop changes to reload data (if ID changes while component is open)
watch(() => props.userId, (newId) => {
  if (newId) {
    fetchUser(newId);
  } else {
    resetForm();
  }
}, { immediate: true });

const saveUser = async () => {
  loading.value = true;
  errorMessage.value = '';

  try {
    const payload = { ...user.value };

    // Remove password if empty during edit
    if (isEditMode.value && !payload.password) {
      delete payload.password;
    }

    if (isEditMode.value) {
      // ✅ Update
      await api.put(`users/${props.userId}/`, payload);
    } else {
      // ✅ Create
      await api.post('users/', payload);
    }

    emit('saved');

  } catch (error) {
    console.error('Save error:', error);

    if (error.response?.data) {
      errorMessage.value = JSON.stringify(error.response.data);
    } else {
      errorMessage.value = 'Failed to save user.';
    }
  } finally {
    loading.value = false;
  }
};


const cancel = () => {
  emit('close');
};
</script>