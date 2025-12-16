<template>
    <v-card>
        <v-toolbar color="primary">
            <v-btn icon @click="$emit('close')">
                <v-icon>mdi-close</v-icon>
            </v-btn>
            <v-toolbar-title>Import Order Excel</v-toolbar-title>
        </v-toolbar>

        <v-form @submit.prevent="uploadFile" ref="form">
            <v-card-text>
                <v-container>
                    <v-alert type="info" class="mb-4" density="compact" variant="tonal">
                        Please upload the "ETD Checklist" Excel file.
                    </v-alert>
                </v-container>
                <v-file-input v-model="files" label="Select Excel File" accept=".xlsx, .xls, .csv"
                    prepend-icon="mdi-microsoft-excel" variant="outlined" show-size
                    :rules="[v => !!v || 'File is required']" required></v-file-input>

                <v-alert v-if="errorMessage" type="error" class="mt-3" closable>
                    {{ errorMessage }}
                </v-alert>
            </v-card-text>

            <v-divider></v-divider>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn variant="text" @click="$emit('close')">Cancel</v-btn>
                <v-btn color="primary" type="submit" :loading="loading" prepend-icon="mdi-cloud-upload">
                    Upload & Process
                </v-btn>
            </v-card-actions>
        </v-form>
    </v-card>

</template>

<script setup>
import { ref } from 'vue';
import api from '@/api';

const emit = defineEmits(['close', 'saved']);

const files = ref(null);
const loading = ref(false);
const errorMessage = ref('');

const uploadFile = async () => {
    if (!files.value) {
        errorMessage.value = "Please select a file first.";
        return;
    }

    loading.value = true;

    try {
        const formData = new FormData();
        formData.append('file', files.value);

        await api.post('orders/', formData);
        emit('saved');
    } catch (error) {
        errorMessage.value =
            error.response?.data?.detail ||
            "Failed to upload file.";
    } finally {
        loading.value = false;
    }
};

</script>