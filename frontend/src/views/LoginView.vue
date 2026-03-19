<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import userService from '../services/userService';
import { useRouter, useRoute } from 'vue-router';
import logo from '../assets/logo.svg';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const username = ref('');
const password = ref('');
const email = ref('');
const resetToken = ref('');
const newPassword = ref('');
const error = ref(null);
const message = ref(null);
const view = ref('login'); // 'login', 'forgot', 'reset'

onMounted(() => {
  const token = route.query.token;
  if (token) {
    resetToken.value = token;
    view.value = 'reset';
  }
});

const handleLogin = async () => {
  error.value = null;
  message.value = null;
  try {
    await authStore.login(username.value, password.value);
    router.push('/');
  } catch (err) {
    error.value = 'Invalid username or password';
  }
};

const handleForgotPassword = async () => {
  error.value = null;
  message.value = null;
  try {
    const response = await userService.forgotPassword(email.value);
    message.value = response.data.msg;
  } catch (err) {
    error.value = 'Failed to process request';
  }
};

const handleResetPassword = async () => {
  error.value = null;
  message.value = null;
  try {
    await userService.resetPassword({
      token: resetToken.value,
      password: newPassword.value
    });
    message.value = 'Password reset successfully. You can now login.';
    view.value = 'login';
  } catch (err) {
    error.value = err.response?.data?.msg || 'Failed to reset password';
  }
};
</script>

<template>
  <div class="min-h-screen flex flex-col md:flex-row bg-[var(--color-background)]">
    <!-- Branding Section -->
    <div class="md:w-1/3 lg:w-2/5 bg-[var(--bg-deep-wave)] flex flex-col items-center justify-center p-8 text-primary relative overflow-hidden">
      <!-- Decorative background elements -->
      <div class="absolute top-[-10%] left-[-10%] w-64 h-64 bg-white opacity-5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-secondary opacity-10 rounded-full blur-3xl"></div>
      
      <div class="relative z-10 flex flex-col items-center text-center">
        <img :src="logo" alt="Surf Accounting Logo" class="h-24 w-24 md:h-32 md:w-32 mb-8" />
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight mb-2 drop-shadow-md">
          Surf Accounting
        </h1>
        <p class="text-lg md:text-xl text-primary/80 font-medium">
          Ride the wave of your finances
        </p>
      </div>
      
      <!-- Bottom attribution on desktop -->
      <div class="absolute bottom-8 text-sm text-primary/60 hidden md:block">
        &copy; 2026 Surf Accounting. All rights reserved.
      </div>
    </div>

    <!-- Login/Forms Section -->
    <div class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="max-w-md w-full">
        <!-- Login Form -->
        <div v-if="view === 'login'" class="space-y-8 animate-fade-in">
          <div>
            <h2 class="text-3xl font-extrabold text-on-surface">
              Welcome back
            </h2>
            <p class="mt-2 text-muted font-medium">
              Please enter your details to sign in
            </p>
          </div>
          
          <form class="space-y-6" @submit.prevent="handleLogin">
            <div class="space-y-4">
              <div class="form-group">
                <label for="username" class="form-label">Username</label>
                <input
                  id="username"
                  v-model="username"
                  name="username"
                  type="text"
                  required
                  class="form-input"
                  placeholder="Enter your username"
                />
              </div>
              <div class="form-group">
                <label for="password" class="form-label">Password</label>
                <input
                  id="password"
                  v-model="password"
                  name="password"
                  type="password"
                  required
                  class="form-input"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div class="flex items-center justify-end">
              <a href="#" @click.prevent="view = 'forgot'" class="text-sm font-bold text-primary hover:opacity-80 transition-opacity">
                Forgot password?
              </a>
            </div>

            <button type="submit" class="btn-primary w-full py-3 text-lg font-bold shadow-lg">
              Sign in
            </button>
            
            <p v-if="error" class="text-center text-sm text-error font-bold">
              {{ error }}
            </p>
            <p v-if="message" class="text-center text-sm text-success font-bold">
              {{ message }}
            </p>
          </form>
        </div>

        <!-- Forgot Password Form -->
        <div v-if="view === 'forgot'" class="space-y-8 animate-fade-in">
          <div>
            <button @click="view = 'login'" class="flex items-center text-primary font-bold mb-4 hover:translate-x-[-4px] transition-transform">
              <span class="material-icons mr-1">arrow_back</span> Back
            </button>
            <h2 class="text-3xl font-extrabold text-on-surface">
              Forgot password?
            </h2>
            <p class="mt-2 text-muted font-medium">
              Don't worry, we'll send you reset instructions.
            </p>
          </div>
          
          <form class="space-y-6" @submit.prevent="handleForgotPassword">
            <div class="form-group">
              <label for="email" class="form-label">Email address</label>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                class="form-input"
                placeholder="your@email.com"
              />
            </div>

            <button type="submit" class="btn-primary w-full py-3 text-lg font-bold shadow-lg">
              Send reset link
            </button>

            <p v-if="error" class="text-center text-sm text-error font-bold">
              {{ error }}
            </p>
            <p v-if="message" class="text-center text-sm text-success font-bold">
              {{ message }}
            </p>
          </form>
        </div>

        <!-- Reset Password Form -->
        <div v-if="view === 'reset'" class="space-y-8 animate-fade-in">
          <div>
            <h2 class="text-3xl font-extrabold text-on-surface">
              Set new password
            </h2>
            <p class="mt-2 text-muted font-medium">
              Choose a strong password for your account.
            </p>
          </div>
          
          <form class="space-y-6" @submit.prevent="handleResetPassword">
            <div class="form-group">
              <label for="newPassword" class="form-label">New Password</label>
              <input
                id="newPassword"
                v-model="newPassword"
                type="password"
                required
                class="form-input"
                placeholder="••••••••"
              />
            </div>

            <button type="submit" class="btn-primary w-full py-3 text-lg font-bold shadow-lg">
              Update password
            </button>

            <p v-if="error" class="text-center text-sm text-error font-bold">
              {{ error }}
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
