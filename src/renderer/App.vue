<template>
  <AppLayout>
    <template #sidebar>
      <Sidebar />
    </template>
    <template #chat>
      <ChatView />
    </template>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from './components/layout/AppLayout.vue'
import Sidebar from './components/sidebar/Sidebar.vue'
import ChatView from './components/chat/ChatView.vue'
</script>
