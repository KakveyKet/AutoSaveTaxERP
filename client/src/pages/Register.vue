<template>
  <v-container class="fill-height bg-grey-lighten-4" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-10 rounded-lg pa-4">
          <!-- Header -->
          <div class="text-center mb-6 mt-4">
            <v-avatar color="secondary" size="64" class="mb-4 elevation-2">
              <v-icon icon="mdi-account-plus" size="32" color="white"></v-icon>
            </v-avatar>
            <h2 class="text-h4 font-weight-bold text-secondary">
              Create Account
            </h2>
            <div class="text-subtitle-1 text-medium-emphasis">
              Join AutoSave ERP
            </div>
          </div>

          <v-card-text>
            <v-form @submit.prevent="handleRegister" ref="form" v-model="valid">
              <!-- Username -->
              <v-text-field
                v-model="formData.username"
                label="Username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                color="secondary"
                class="mb-2"
                :rules="[rules.required, rules.min3]"
              ></v-text-field>

              <!-- Email -->
              <v-text-field
                v-model="formData.email"
                label="Email Address"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                color="secondary"
                class="mb-2"
                :rules="[rules.required, rules.email]"
              ></v-text-field>

              <!-- Password -->
              <v-text-field
                v-model="formData.password"
                label="Password"
                prepend-inner-icon="mdi-lock"
                :type="visible ? 'text' : 'password'"
                :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="visible = !visible"
                variant="outlined"
                color="secondary"
                class="mb-4"
                :rules="[rules.required, rules.min6]"
              ></v-text-field>

              <!-- Error Alert -->
              <v-expand-transition>
                <div v-if="error">
                  <v-alert
                    type="error"
                    variant="tonal"
                    class="mb-4"
                    closable
                    @click:close="error = ''"
                  >
                    {{ error }}
                  </v-alert>
                </div>
              </v-expand-transition>

              <!-- Submit -->
              <v-btn
                block
                color="secondary"
                size="large"
                type="submit"
                :loading="loading"
                class="text-uppercase font-weight-bold elevation-2"
                height="48"
              >
                Register
              </v-btn>
            </v-form>
          </v-card-text>

          <v-card-actions class="justify-center mt-2 mb-4">
            <span class="text-body-2 text-grey">
              Already have an account?
              <router-link
                to="/login"
                class="text-secondary font-weight-bold text-decoration-none"
                >Login here</router-link
              >
            </span>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

const router = useRouter();
const form = ref(null);
const valid = ref(false);
const loading = ref(false);
const error = ref("");
const visible = ref(false);

const formData = ref({
  username: "",
  email: "",
  password: "",
});

const rules = {
  required: (v) => !!v || "Required.",
  min3: (v) => v.length >= 3 || "Min 3 characters.",
  min6: (v) => v.length >= 6 || "Min 6 characters.",
  email: (v) => /.+@.+\..+/.test(v) || "Invalid email.",
};

const handleRegister = async () => {
  if (!valid.value) return;

  loading.value = true;
  error.value = "";

  try {
    // CRITICAL FIX: The URL must end with '/' to avoid Django 500/Redirect error
    await api.post("register/", {
      username: formData.value.username,
      email: formData.value.email,
      password: formData.value.password,
      role: "user", // Default role
    });

    // On success, redirect to login
    router.push("/login");
  } catch (err) {
    console.error("Registration Error:", err);
    if (err.response && err.response.data) {
      // Handle Django validation errors (e.g., "username already exists")
      const data = err.response.data;
      if (data.username) error.value = `Username: ${data.username[0]}`;
      else if (data.email) error.value = `Email: ${data.email[0]}`;
      else if (data.password) error.value = `Password: ${data.password[0]}`;
      else error.value = "Registration failed. Please check your inputs.";
    } else {
      error.value = "Server error. Please try again later.";
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.fill-height {
  background: #f5f5f5;
}
</style>
