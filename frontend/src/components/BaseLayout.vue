<template>
  <div class="app-layout min-h-screen bg-[var(--color-background)]">
    <div class="header-shadow no-print"></div>

    <!-- Header -->
    <header class="pt-3 mb-3 flex items-center z-[1000] h-[56px] w-full no-print">
      <!-- Desktop Logo -->
      <div class="logo hidden lg:block w-[var(--width-sidenav)] px-6 flex-shrink-0 my-auto">
        <template v-if="settings?.app_logo_url">
          <img :src="getFullImageUrl(settings.app_logo_url)" alt="Surf Accounting" class="max-h-8 max-w-full object-contain" />
        </template>
        <div v-else class="flex items-center gap-3">
          <img :src="defaultLogo" alt="Surf Accounting" class="max-h-8 max-w-full object-contain" />
          <span class="font-bold text-xl">Surf Accounting</span>
        </div>
      </div>
      
      <!-- Header Content Area -->
      <div class="flex-1 flex items-center justify-between px-3 md:px-4 min-w-0">
        <!-- Left: Mobile Toggle + Back + Title -->
        <div class="flex items-center gap-2 min-w-0">
          <div class="lg:hidden">
            <div class="pill-nav flex items-center flex-shrink-0">
              <button
                @click="toggleMobileNav"
                class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8"
                aria-label="Toggle navigation"
              >
                <span class="material-icons">menu</span>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2 min-w-0">
            <div v-if="backPath" class="pill-nav flex items-center flex-shrink-0">
              <RouterLink 
                :to="backPath" 
                class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8"
                title="Go Back"
              >
                <span class="material-icons text-[22px]">arrow_back</span>
              </RouterLink>
            </div>
            <span class="truncate font-semibold text-lg">{{ pageTitle }}</span>
          </div>
        </div>

        <!-- Right: Actions + Account -->
        <div class="fixed top-0 right-0 mr-3 md:mr-4 mt-3 flex gap-2 items-center z-[1000]">
          <div id="navbar-actions" class="flex items-center gap-2"></div>

          <!-- Account button pill -->
          <div class="relative">
            <div class="pill-nav flex">
              <button
                class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8"
                @click.stop="toggleProfileMenu"
                title="Account"
              >
                <span class="material-icons text-[35px] font-[200]">account_circle</span>
              </button>
            </div>

            <!-- Profile Dropdown -->
            <div 
              v-if="isProfileMenuOpen"
              class="absolute right-0 mt-2 w-64 bg-white rounded-[14px] shadow-lg border border-gray-100 overflow-hidden z-[1010]"
              @click.stop
            >
              <div class="p-4 border-b border-gray-100 bg-gray-50/30">
                <p class="text-sm font-bold text-[var(--color-on-surface)] truncate">{{ profile.username || 'User' }}</p>
                <p class="text-xs text-gray-500 truncate" v-if="profile.email">{{ profile.email }}</p>
              </div>
              <div class="py-1">
                <button
                  @click="handleLogout"
                  class="w-full text-left px-4 py-2 text-sm text-error hover:bg-error/5 flex items-center gap-2 transition-colors"
                >
                  <span class="material-icons text-[20px]">logout</span>
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="fixed flex left-0 mt-3 appear-on-scroll" style="z-index: 1000;">
      <div class="pill-nav hidden lg:flex items-center">
        <RouterLink
          :to="backPath"
          class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8"
          title="Go Back"
        >
          <span class="material-icons text-[22px]">arrow_back</span>
        </RouterLink>
      </div>
    </div>

    <!-- Mobile Drawer Overlay -->
    <div 
      v-if="isMobileNavOpen" 
      class="fixed inset-0 bg-black/32 z-[1050]" 
      @click="closeMobileNav"
    ></div>

    <!-- Mobile Drawer -->
    <div 
      class="fixed top-0 left-0 h-full w-[85%] max-w-[300px] bg-white z-[1060] transition-transform duration-300 transform"
      :class="isMobileNavOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="p-4 flex justify-between items-center">
        <template v-if="settings?.app_logo_url">
          <img :src="getFullImageUrl(settings.app_logo_url)" alt="Surf Accounting" class="max-h-8 max-w-[80%] object-contain" />
        </template>
        <img v-else :src="defaultLogo" alt="Surf Accounting" class="max-h-8 max-w-[80%] object-contain" />
        <button @click="closeMobileNav" class="w-[40px] h-[40px] flex items-center justify-center rounded-full hover:bg-primary/8">
          <span class="material-icons">close</span>
        </button>
      </div>
      <nav class="p-2 ps-0">
        <RouterLink
          v-for="link in navLinks"
          :key="link.path"
          :to="link.path"
          class="flex items-center px-4 py-3 rounded-r-[100px] mb-1 hover:bg-primary/5 transition-colors"
          exact-active-class="bg-primary/10 text-primary font-bold"
          @click="closeMobileNav"
        >
          <span class="material-icons mr-4">{{ link.icon }}</span>
          {{ link.label }}
        </RouterLink>
      </nav>
    </div>

    <main class="flex">
      <!-- Desktop Sidebar -->
      <div class="sidebar hidden lg:block w-[var(--width-sidenav)] h-[calc(100vh-56px)] overflow-y-auto flex-shrink-0 z-[4] no-print sticky" style="top: 72px;">
        <nav class="p-0">
          <RouterLink
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="flex items-center px-6 py-3 rounded-r-[100px] mb-1 text-[var(--color-on-surface)] hover:bg-secondary/10 transition-colors"
            exact-active-class="bg-secondary/10 text-secondary font-bold"
          >
            <span class="material-icons mr-4">{{ link.icon }}</span>
            {{ link.label }}
          </RouterLink>
        </nav>
      </div>

      <!-- Content Area -->
      <div class="content flex-1 px-3 md:px-4 pb-4 max-w-full overflow-hidden">
        <RouterView v-if="isMounted" />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import settingsService from '../services/settingsService'
import { getFullImageUrl } from '../utils/imageUtils'
import defaultLogo from '../assets/logo.svg'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const profile = computed(() => authStore.user || {})
const pageTitle = ref("Dashboard")
const backPath = computed(() => route.meta?.backPath || null)
const isMobileNavOpen = ref(false)
const isProfileMenuOpen = ref(false)
const isMounted = ref(false)
const settings = ref(null)

const fetchSettings = async () => {
  try {
    const response = await settingsService.getSettingsList()
    if (response.data.settings && response.data.settings.length > 0) {
      settings.value = response.data.settings[0]
    }
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  }
}

// Scroll state
const scrollY = ref(0)
const handleScroll = () => {
  scrollY.value = window.scrollY
}

const scrollPastHeader = computed(() => scrollY.value >= 80 ? 1 : 0)
const scrollOpacity = computed(() => (Math.min(scrollY.value / 80, 1)).toFixed(2))

onMounted(() => {
  isMounted.value = true
  window.addEventListener('scroll', handleScroll)
  window.addEventListener('click', closeProfileMenu)
  
  fetchSettings()

  watch([scrollPastHeader, scrollOpacity], ([newPastHeader, newOpacity]) => {
    document.documentElement.style.setProperty('--scroll-past-header', newPastHeader)
    document.documentElement.style.setProperty('--scroll-opacity', newOpacity)
  }, { immediate: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('click', closeProfileMenu)
  document.documentElement.style.removeProperty('--scroll-past-header')
  document.documentElement.style.removeProperty('--scroll-opacity')
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const toggleMobileNav = () => {
  isMobileNavOpen.value = !isMobileNavOpen.value
}

const closeMobileNav = () => {
  isMobileNavOpen.value = false
}

const toggleProfileMenu = () => {
  isProfileMenuOpen.value = !isProfileMenuOpen.value
}

const closeProfileMenu = () => {
  isProfileMenuOpen.value = false
}

watch(() => route.meta, (meta) => {
  pageTitle.value = meta?.pageTitle || "Dashboard"
}, { immediate: true })

const navLinks = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/customers', label: 'Customers', icon: 'people' },
  { path: '/vendors', label: 'Vendors', icon: 'store' },
  { path: '/items', label: 'Products & Services', icon: 'inventory_2' },
  { path: '/invoices', label: 'Invoices', icon: 'description' },
  { path: '/bills', label: 'Bills', icon: 'receipt_long' },
  { path: '/journals', label: 'Journals', icon: 'book' },
  { path: '/reports', label: 'Reports', icon: 'assessment' },
  { path: '/settings', label: 'Settings', icon: 'settings' },
]
</script>
