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
                :isActive="$store.getters['preferences/saved'].upcoming_deadline_notifications"
                class="float-right"
                @parentActive="e => changePreference('upcoming_deadline_notifications', e)"
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
                    :selected="$store.getters['preferences/saved'][preference['key']]"
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
        changePreference (key, value) {
            const toUpdate = {}
            toUpdate[key] = value
            this.$store.commit('preferences/CHANGE_PREFERENCES', toUpdate)
        },
    },
}
</script>
