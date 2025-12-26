<template>
  <v-container class="fill-height justify-center">
    <v-card width="600" class="pa-4">
      <v-card-title class="text-h5 mb-4">
        DigitalOcean Upload Test
      </v-card-title>

      <v-card-text>
        <v-alert type="success" variant="tonal" class="mb-4">
          You are authenticated. Ready to upload to DigitalOcean Spaces.
        </v-alert>

        <!-- FILE INPUT -->
        <v-file-input
          v-model="selectedFile"
          label="Select Excel File (.xlsx)"
          accept=".xlsx,.xls"
          variant="outlined"
          prepend-icon="mdi-microsoft-excel"
          show-size
        />

        <!-- PROGRESS -->
        <v-progress-linear
          v-if="loading"
          indeterminate
          color="primary"
          class="my-4"
        />

        <!-- RESULT -->
        <v-alert
          v-if="uploadResult"
          :type="isCloudUrl ? 'success' : 'warning'"
          variant="outlined"
          class="mt-4"
        >
          <div class="text-subtitle-1 font-weight-bold">
            Upload Complete
          </div>
          <div class="text-caption mt-1">
            ID: {{ uploadResult.id }}
          </div>
          <div class="text-caption mt-1">
            URL:
            <a :href="uploadResult.file" target="_blank">
              {{ uploadResult.file }}
            </a>
          </div>

          <div
            v-if="isCloudUrl"
            class="mt-2 font-weight-bold text-blue"
          >
            🌊 Verified: DigitalOcean Spaces
          </div>

          <div
            v-else
            class="mt-2 font-weight-bold text-orange"
          >
            ⚠️ Warning: Not DigitalOcean URL
          </div>
        </v-alert>

        <!-- ERROR -->
        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mt-4"
        >
          {{ error }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          color="primary"
          variant="elevated"
          :disabled="!selectedFile || loading"
          :loading="loading"
          @click="uploadFile"
        >
          Upload to Cloud
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// ======================
// CONFIG
// ======================
const API_URL = 'http://127.0.0.1:8000/api'

// ======================
// STATE
// ======================
const loading = ref(false)
const error = ref('')
const selectedFile = ref(null)
const uploadResult = ref(null)
const token = ref('')

// ======================
// GET TOKEN (Already Logged In)
// ======================
onMounted(() => {
  token.value = localStorage.getItem('access_token')
})

// ======================
// COMPUTED
// ======================
const isCloudUrl = computed(() => {
  return uploadResult.value?.file?.includes(
    'digitaloceanspaces.com'
  )
})

const uploadFile = async () => {
  if (!selectedFile.value) return

  loading.value = true
  error.value = ''
  uploadResult.value = null

  try {
    const formData = new FormData()

    // v-file-input returns array sometimes
    const file = Array.isArray(selectedFile.value)
      ? selectedFile.value[0]
      : selectedFile.value

    formData.append('file', file)

    const response = await axios.post(
      `${API_URL}/orders/`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      }
    )

    uploadResult.value = response.data
    console.log('Upload success:', response.data)
  } catch (err) {
    console.error(err)
    error.value =
      err.response?.data?.detail ||
      'Upload failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
