<template>
    <div>
        <h4 class="theme-h4 mb-2 mt-4">
            <span>Email notifications</span>
        </h4>
        <b-card
            :class="$root.getBorderClass($route.params.uID)"
            class="no-hover multi-form"
        >
            <!-- TODO: enable once comment and grade notifications available - <toggle-switch
                class="float-right"
                :isActive="$store.getters['preferences/gradeNotifications']"
                @parentActive="getGradeNotification"/>
            <h2 class="theme-h2 field-heading multi-form">Grade updates</h2>
            <toggle-switch
                class="float-right"
                :isActive="$store.getters['preferences/commentNotifications']"
                @parentActive="getCommentNotification"/>
            <h2 class="theme-h2 field-heading multi-form">Comments</h2> -->
            <toggle-switch
                :isActive="$store.getters['preferences/upcomingDeadlineNotifications']"
                class="float-right"
                @parentActive="getUpcomingDeadlineNotification"
            />
            <h2 class="theme-h2 field-heading multi-form">
                Upcoming deadlines
            </h2>
        </b-card>
    </div>
</template>

<script>
import toggleSwitch from '@/components/assets/ToggleSwitch.vue'
import preferencesAPI from '@/api/preferences.js'

export default {
    components: {
        toggleSwitch,
    },
    props: ['userData'],
    methods: {
        getGradeNotification (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { grade_notifications: isActive },
                { customSuccessToast: 'Grade notification setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit('preferences/SET_GRADE_NOTIFICATION', preferences.grade_notifications)
                })
        },
        getCommentNotification (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { comment_notifications: isActive },
                { customSuccessToast: 'Comment notification setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit('preferences/SET_COMMENT_NOTIFICATION', preferences.comment_notifications)
                })
        },
        getUpcomingDeadlineNotification (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { upcoming_deadline_notifications: isActive },
                { customSuccessToast: 'Upcoming deadline notification setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit(
                        'preferences/SET_UPCOMING_DEADLINE_NOTIFICATION', preferences.upcoming_deadline_notifications)
                })
        },
    },
}
</script>
