<template>
    <content-single-column>
        <h1 class="theme-h1">
            <span>Login</span>
        </h1>
        <login-form @handleAction="handleLoginSucces"/>
        <custom-footer/>
    </content-single-column>
</template>

<script>
import contentSingleColumn from '@/components/columns/ContentSingleColumn.vue'
import customFooter from '@/components/assets/Footer.vue'
import loginForm from '@/components/account/LoginForm.vue'
import routerConstraints from '@/utils/constants/router_constraints.js'

export default {
    name: 'Login',
    components: {
        contentSingleColumn,
        customFooter,
        loginForm,
    },
    data () {
        return {
            username: '',
            password: '',
        }
    },
    methods: {
        handleLoginSucces () {
            if (this.$root.previousPage === null || this.$root.previousPage.name === null
                || routerConstraints.PERMISSIONLESS_CONTENT.has(this.$root.previousPage.name)) {
                this.$router.push({ name: 'Home' })
            } else {
                this.$router.push({ name: this.$root.previousPage.name, params: this.$root.previousPage.params })
            }
        },
    },
}
</script>
