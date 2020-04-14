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
            <div
                v-for="preference in preferences"
                :key="preference['key']"
            >
                <br/>
                <notify-switch
                    :selected="$store.getters['preferences/databasePreferences'][preference['key']]"
                    class="float-right"
                    @changedSelected="e => changePreference(preference['key'], e)"
                />
                <h2 class="theme-h2 field-heading multi-form">
                    {{ preference['name'] }}
                    <tooltip
                        :tip="preference['tooltip']"
                    />
                </h2>
            </div>
        </b-card>
    </div>
</template>

<script>
import toggleSwitch from '@/components/assets/ToggleSwitch.vue'
import notifySwitch from '@/components/assets/NotifySwitch.vue'
import preferencesAPI from '@/api/preferences.js'
import tooltip from '@/components/assets/Tooltip.vue'

export default {
    components: {
        toggleSwitch,
        notifySwitch,
        tooltip,
    },
    props: ['userData'],
    data () {
        return {
            preferences: [
                {
                    name: 'New course',
                    key: 'new_course_notifications',
                    tooltip: 'Receive an email when you are added to a new course.',
                },
                {
                    name: 'New assignment',
                    key: 'new_assignment_notifications',
                    tooltip: 'Receive an email when a new assignment is published.',
                },
                {
                    name: 'Timeline updates',
                    key: 'new_preset_node_notifications',
                    tooltip: 'Receive an email when a new node gets added to your timeline.',
                },
                {
                    name: 'New entry',
                    key: 'new_entry_notifications',
                    tooltip: 'Receive an email when a new entry is posted.',
                },
                {
                    name: 'New grade',
                    key: 'new_grade_notifications',
                    tooltip: 'Receive an email when you receive a grade.',
                },
                {
                    name: 'New comment',
                    key: 'new_comment_notifications',
                    tooltip: 'Receive an email when a new comment is posted.',
                },
            ],
        }
    },
    methods: {
        changePreference (name, period) {
            const toUpdate = {}
            toUpdate[name] = period
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                toUpdate,
                { customSuccessToast: 'Email setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit('preferences/HYDRATE_PREFERENCES', preferences, { root: true })
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
