<template>
    <div>
        <h4 class="theme-h4 mb-2 mt-4">
            <span>Email notifications</span>
        </h4>
        <b-card
            :class="$root.getBorderClass($route.params.uID)"
            class="no-hover multi-form"
        >
            <toggle-switch
                :isActive="$store.getters['preferences/upcomingDeadlineNotifications']"
                class="float-right"
                @parentActive="getUpcomingDeadlineNotification"
            />
            <h2 class="theme-h2 field-heading multi-form">
                Upcoming deadlines
            </h2>
            <br/>
            <notify-switch
                :selected="$store.getters['preferences/commentNotifications']"
                class="float-right"
                @changedSelected="setCommentNotification"
            />
            <h2 class="theme-h2 field-heading multi-form">
                New comments
            </h2>
            <br/>
            <notify-switch
                :selected="$store.getters['preferences/gradeNotifications']"
                class="float-right"
                @changedSelected="setGradeNotification"
            />
            <h2 class="theme-h2 field-heading multi-form">
                New grades
            </h2>
        </b-card>
    </div>
</template>

<script>
import toggleSwitch from '@/components/assets/ToggleSwitch.vue'
import notifySwitch from '@/components/assets/NotifySwitch.vue'
import preferencesAPI from '@/api/preferences.js'

export default {
    components: {
        toggleSwitch,
        notifySwitch,
    },
    props: ['userData'],
    methods: {
        setGradeNotification (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { new_grade_notifications: isActive },
                { customSuccessToast: 'Grade notification setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit('preferences/SET_GRADE_NOTIFICATION', preferences.new_grade_notifications)
                })
        },
        setCommentNotification (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { new_comment_notifications: isActive },
                { customSuccessToast: 'Comment notification setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit('preferences/SET_COMMENT_NOTIFICATION', preferences.new_comment_notifications)
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
