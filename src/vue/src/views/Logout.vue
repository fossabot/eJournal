<template>
    <h2 class="theme-h2">
        Logging out
    </h2>
</template>

<script>
// TODO Move to route only logic
export default {
    created () {
        this.$store.dispatch('user/logout')
        this.$router.push({ name: 'Guest' })
    },
}
</script>
