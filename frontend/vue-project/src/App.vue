<template>
  <div class="app-shell">
    <RouterView />
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--slate-50);
  color: var(--slate-900);
}
</style>
