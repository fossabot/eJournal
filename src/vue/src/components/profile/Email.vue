<template>
    <div>
        <b-input-group class="multi-form">
            <b-input
                v-model="email"
                :readonly="$store.getters['user/verifiedEmail']"
                class="theme-input"
                type="text"
            />
            <b-input-group-text
                slot="append"
                class="theme-input input-append-icon round-border"
            >
                <icon
                    v-if="!$store.getters['user/verifiedEmail']"
                    v-b-tooltip:hover="(showEmailValidationInput) ? 'Enter the email verification token below.' :
                        'Click to verify your email!'"
                    :name="(showEmailValidationInput) ? 'check' : 'paper-plane'"
                    @click.native="requestEmailVerification"
                />
                <icon
                    v-if="$store.getters['user/verifiedEmail']"
                    v-b-tooltip:hover="'Your email is verified!'"
                    name="check"
                    class="checked-icon"
                />
            </b-input-group-text>
        </b-input-group>

        <b-input-group
            v-if="!$store.getters['user/verifiedEmail'] && showEmailValidationInput"
            class="multi-form"
        >
            <b-input
                v-model="emailVerificationToken"
                v-b-tooltip:hover="(emailVerificationTokenMessage) ? emailVerificationTokenMessage : 'Enter your token'"
                class="theme-input"
                required
                placeholder="Enter the email verification token."
            />
            <b-input-group-text
                slot="append"
                class="theme-input input-append-icon round-border"
            >
                <icon
                    v-b-tooltip:hover="'Validate verification code.'"
                    name="paper-plane"
                    @click.native="verifyEmail"
                />
            </b-input-group-text>
        </b-input-group>
    </div>
</template>

<script>
import userAPI from '@/api/user.js'

export default {
    data () {
        return {
            showEmailValidationInput: false,
            emailVerificationToken: null,
            emailVerificationTokenMessage: null,
        }
    },
    computed: {
        email: {
            get () {
                return this.$store.getters['user/email']
            },
            set (value) {
                this.$store.commit('user/SET_EMAIL', value)
            },
        },
    },
    methods: {
        requestEmailVerification () {
            if (!this.showEmailValidationInput) {
                userAPI.requestEmailVerification(this.email, { responseSuccessToast: true })
                    .then(() => { this.showEmailValidationInput = true })
            }
        },
        verifyEmail () {
            userAPI.verifyEmail(
                this.$store.getters['user/username'],
                this.emailVerificationToken,
                { responseSuccessToast: true },
            )
                .then(() => {
                    this.$store.commit('user/EMAIL_VERIFIED')
                    this.showEmailValidationInput = false
                })
                .catch(() => { this.emailVerificationTokenMessage = 'Invalid token' })
        },
    },
}
</script>
