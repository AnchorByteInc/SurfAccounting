<template>
  <div class="max-w-2xl mx-auto pb-12">
    <div class="card">
      <h2 class="text-xl font-bold mb-6">Business & Branding Settings</h2>
      <form @submit.prevent="saveSettings" class="space-y-4">
        <div>
          <label class="form-label">Business Name</label>
          <input
            v-model="settings.business_name"
            type="text"
            required
            placeholder="e.g. My Awesome Company"
            class="form-input"
          />
        </div>

        <div>
          <label class="form-label">Business Email</label>
          <input
            v-model="settings.email"
            type="email"
            placeholder="email@example.com"
            class="form-input"
          />
        </div>

        <div>
          <label class="form-label">Address</label>
          <input
            v-model="settings.address"
            type="text"
            placeholder="Business Address"
            class="form-input"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="form-label">City</label>
            <input
              v-model="settings.city"
              type="text"
              placeholder="City"
              class="form-input"
            />
          </div>
          <div>
            <label class="form-label">State</label>
            <input
              v-model="settings.state"
              type="text"
              placeholder="State"
              class="form-input"
            />
          </div>
          <div>
            <label class="form-label">Zip Code</label>
            <input
              v-model="settings.zip"
              type="text"
              placeholder="Zip Code"
              class="form-input"
            />
          </div>
        </div>

        <div>
          <label class="form-label">Default Currency</label>
          <input
            v-model="settings.default_currency"
            type="text"
            required
            maxlength="3"
            placeholder="USD"
            class="form-input w-24"
          />
        </div>

        <div class="pt-4 border-t border-divider">
          <h3 class="text-lg font-bold mb-4">Branding Logos</h3>
          
          <div class="space-y-6">
            <div>
              <label class="form-label">App Logo</label>
              <div class="flex flex-col gap-2">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleFileUpload($event, 'app_logo_url')"
                  class="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded file:border-0
                    file:text-sm file:font-semibold
                    file:bg-primary/10 file:text-primary
                    hover:file:bg-primary/20"
                />
                <p class="text-xs text-muted">Recommended: Horizontal format. This logo appears on your PDFs.</p>
                <div v-if="settings.app_logo_url" class="relative group mt-2 p-4 border rounded bg-gray-50 flex justify-center items-center h-32 overflow-hidden">
                  <img :src="getFullImageUrl(settings.app_logo_url)" alt="App Logo Preview" class="max-h-full max-w-full object-contain" />
                  <button 
                    type="button"
                    @click="settings.app_logo_url = ''"
                    class="absolute top-2 right-2 p-1 bg-white/80 rounded-full shadow hover:bg-white text-error"
                    title="Remove Logo"
                  >
                    <span class="material-icons">delete</span>
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label class="form-label">Invoice Logo</label>
              <div class="flex flex-col gap-2">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleFileUpload($event, 'invoice_logo_url')"
                  class="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded file:border-0
                    file:text-sm file:font-semibold
                    file:bg-primary/10 file:text-primary
                    hover:file:bg-primary/20"
                />
                <p class="text-xs text-muted">Recommended: 1:1 or 2:1 aspect ratio. PNG or SVG preferred.</p>
                <div v-if="settings.invoice_logo_url" class="relative group mt-2 p-4 border rounded bg-gray-50 flex justify-center items-center h-48 overflow-hidden">
                  <img :src="getFullImageUrl(settings.invoice_logo_url)" alt="Invoice Logo Preview" class="max-h-full max-w-full object-contain" />
                  <button 
                    type="button"
                    @click="settings.invoice_logo_url = ''"
                    class="absolute top-2 right-2 p-1 bg-white/80 rounded-full shadow hover:bg-white text-error"
                    title="Remove Logo"
                  >
                    <span class="material-icons">delete</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="pt-6 flex justify-end gap-3">
          <button
            type="button"
            @click="router.back()"
            class="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="submitting"
            class="btn-primary"
          >
            {{ submitting ? 'Saving...' : (settingsId ? 'Save Changes' : 'Create Settings') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import settingsService from '../../services/settingsService';
import { getFullImageUrl } from '../../utils/imageUtils';

const router = useRouter();
const submitting = ref(false);
const settingsId = ref(null);

const settings = ref({
  business_name: '',
  address: '',
  city: '',
  state: '',
  zip: '',
  email: '',
  default_currency: 'USD',
  app_logo_url: '',
  invoice_logo_url: ''
});

const fetchSettings = async () => {
  try {
    const response = await settingsService.getSettingsList();
    if (response.data.settings && response.data.settings.length > 0) {
      const s = response.data.settings[0];
      settings.value = {
        business_name: s.business_name || '',
        address: s.address || '',
        city: s.city || '',
        state: s.state || '',
        zip: s.zip || '',
        email: s.email || '',
        default_currency: s.default_currency || 'USD',
        app_logo_url: s.app_logo_url || '',
        invoice_logo_url: s.invoice_logo_url || ''
      };
      settingsId.value = s.id;
    }
  } catch (error) {
    console.error('Failed to fetch settings:', error);
  }
};

const handleFileUpload = async (event, field) => {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await settingsService.uploadLogo(formData);
    settings.value[field] = response.data.url;
  } catch (error) {
    console.error('Upload failed:', error);
    alert('Failed to upload image.');
  }
};

const saveSettings = async () => {
  submitting.value = true;
  try {
    if (settingsId.value) {
      await settingsService.updateSettings(settingsId.value, settings.value);
    } else {
      await settingsService.createSettings(settings.value);
    }
    router.push('/settings');
  } catch (error) {
    console.error('Failed to save settings:', error);
    alert('Failed to save settings.');
  } finally {
    submitting.value = false;
  }
};

const handleImageError = (e) => {
  console.warn('Invalid image URL:', e.target.src);
};

onMounted(() => {
  fetchSettings();
});
</script>
