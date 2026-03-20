<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[2000] flex items-center justify-center p-4 m-0 bg-black/32"
    @click="close"
  >
    <!-- Modal Content -->
    <div
      class="relative bg-white rounded-[14px] shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]"
      @click.stop
    >
      <!-- Header -->
      <div
        class="p-6 border-b border-gray-100 flex justify-between items-center"
      >
        <h2 class="text-xl font-bold text-[var(--color-on-surface)]">
          {{ title }}
        </h2>
        <button
          @click="close"
          class="p-2 hover:bg-gray-100 rounded-full transition-colors"
        >
          <span class="material-icons">close</span>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 overflow-y-auto space-y-6">
        <div class="bg-primary/5 rounded-[14px] p-4 border border-primary/10">
          <h3 class="font-bold text-primary mb-2 flex items-center gap-2">
            <span class="material-icons text-[20px]">info</span>
            Instructions
          </h3>
          <p class="text-sm text-gray-700 mb-4">
            Please upload a CSV file with the following columns. The first row
            should contain the column names.
          </p>
          <div class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="field in templateFields"
              :key="field"
              class="px-3 py-1 bg-white border border-primary/20 rounded-full text-xs font-medium text-primary"
            >
              {{ field }}
            </span>
          </div>

          <div
            v-if="title.includes('Journal Entries')"
            class="mt-4 p-3 bg-white/50 rounded-lg border border-primary/10"
          >
            <p
              class="text-[11px] font-bold text-primary uppercase tracking-wider mb-1"
            >
              Journal Entry Format Tip:
            </p>
            <p class="text-xs text-gray-600">
              To import multi-line entries: provide the <strong>date</strong>,
              <strong>reference</strong>, and <strong>memo</strong> on the first
              row of the entry. For subsequent lines of the same entry, you can
              leave these fields blank but must keep the
              <strong>account_code</strong> and <strong>debit/credit</strong> on
              each row.
            </p>
          </div>
          <p class="text-xs text-gray-500 mt-4 italic">
            * Required fields must be present and non-empty.
          </p>
        </div>

        <!-- Drop Zone -->
        <div
          class="border-2 border-dashed rounded-[14px] p-10 flex flex-col items-center justify-center transition-colors cursor-pointer"
          :class="
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-gray-200 hover:border-primary/50'
          "
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
        >
          <input
            type="file"
            ref="fileInput"
            class="hidden"
            accept=".csv"
            @change="handleFileSelect"
          />
          <span class="material-icons text-[48px] text-gray-300 mb-4"
            >cloud_upload</span
          >
          <p class="text-sm font-medium text-gray-700">
            {{
              selectedFile
                ? selectedFile.name
                : "Click to upload or drag and drop"
            }}
          </p>
          <p class="text-xs text-gray-400 mt-1">CSV files only</p>
        </div>

        <!-- Results / Errors -->
        <div v-if="results" class="space-y-3">
          <div
            :class="
              results.count > 0
                ? 'bg-green-50 text-green-700'
                : 'bg-red-50 text-red-700'
            "
            class="p-4 rounded-[14px] flex items-center gap-3"
          >
            <span class="material-icons">{{
              results.count > 0 ? "check_circle" : "error"
            }}</span>
            <p class="text-sm font-medium">{{ results.message }}</p>
          </div>

          <div
            v-if="results.errors && results.errors.length > 0"
            class="border border-red-100 rounded-[14px] overflow-hidden"
          >
            <div
              class="bg-red-50 px-4 py-2 border-b border-red-100 text-xs font-bold text-red-700"
            >
              Details / Errors ({{ results.errors.length }})
            </div>
            <ul class="max-h-40 overflow-y-auto p-4 space-y-1 bg-white">
              <li
                v-for="(error, index) in results.errors"
                :key="index"
                class="text-xs text-red-600 flex items-start gap-2"
              >
                <span class="material-icons text-[14px] mt-0.5"
                  >error_outline</span
                >
                {{ error }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div
        class="p-6 border-t border-gray-100 flex justify-end gap-3 bg-gray-50/50"
      >
        <button
          @click="close"
          class="px-6 h-[40px] rounded-full border border-gray-200 text-gray-600 font-medium hover:bg-white transition-colors"
        >
          {{ results ? "Close" : "Cancel" }}
        </button>
        <button
          v-if="!results"
          @click="uploadFile"
          :disabled="!selectedFile || isUploading"
          class="px-6 h-[40px] rounded-full bg-primary text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span
            v-if="isUploading"
            class="material-icons animate-spin text-[20px]"
            >sync</span
          >
          {{ isUploading ? "Importing..." : "Import Now" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import api from "../services/api";

const props = defineProps({
  isOpen: Boolean,
  title: String,
  uploadUrl: String,
  templateFields: Array,
});

const emit = defineEmits(["close", "success"]);

const isDragging = ref(false);
const selectedFile = ref(null);
const isUploading = ref(false);
const results = ref(null);
const fileInput = ref(null);

const close = () => {
  if (isUploading.value) return;
  emit("close");
  // Reset state after a delay
  setTimeout(() => {
    selectedFile.value = null;
    results.value = null;
    if (fileInput.value) fileInput.value.value = "";
  }, 300);
};

const handleFileSelect = (event) => {
  const file = event.target.files[0];
  if (file && file.name.endsWith(".csv")) {
    selectedFile.value = file;
    results.value = null;
  }
};

const handleDrop = (event) => {
  isDragging.value = false;
  const file = event.dataTransfer.files[0];
  if (file && file.name.endsWith(".csv")) {
    selectedFile.value = file;
    results.value = null;
  }
};

const uploadFile = async () => {
  if (!selectedFile.value) return;

  isUploading.value = true;
  const formData = new FormData();
  formData.append("file", selectedFile.value);

  try {
    const response = await api.post(props.uploadUrl, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    results.value = response.data;
    if (response.data.count > 0) {
      emit("success");
    }
  } catch (error) {
    console.error("Import failed:", error);
    results.value = {
      message: error.response?.data?.message || "Failed to process CSV file.",
      errors: error.response?.data?.errors || [error.message],
      count: 0,
    };
  } finally {
    isUploading.value = false;
  }
};
</script>
