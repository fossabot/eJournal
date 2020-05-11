<template>
    <div>
        <h4 class="theme-h4 mb-2 mt-4">
            <span>Email notifications</span>
        </h4>
        <b-card
            :class="$root.getBorderClass($route.params.uID)"
            class="no-hover multi-form"
        >
            <b-row>
                <b-col
                    col="3"
                    class="text-center"
                >
                    <icon
                        name="bell"
                        class="fill-grey shift-up-3 mr-1"
                    />
                    Immediately
                </b-col>
                <b-col
                    col="3"
                    class="text-center"
                >
                    <icon
                        name="clock"
                        class="fill-grey shift-up-3 mr-1"
                    />
                    Daily summarry
                </b-col>
                <b-col
                    col="3"
                    class="text-center"
                >
                    <icon
                        name="calendar"
                        class="fill-grey shift-up-3 mr-1"
                    />
                    Weekly summary
                </b-col>
                <b-col
                    col="3"
                    class="text-center"
                >
                    <icon
                        name="times"
                        class="fill-grey shift-up-3 mr-1"
                    />
                    No notifications
                </b-col>
            </b-row>
            <hr/>
            <div class="clearfix multi-form">
                <radio-button
                    v-model="$store.getters['preferences/saved'].upcoming_deadline_notifications"
                    :options="[
                        {
                            value: true,
                            icon: 'check',
                            class: 'add-button',
                        },
                        {
                            value: false,
                            icon: 'times',
                            class: 'delete-button',
                        },
                    ]"
                    class="float-right"
                    @input="e => changePreference('upcoming_deadline_notifications', e)"
                />
                <h2 class="theme-h2 field-heading multi-form">
                    Upcoming deadlines
                    <tooltip
                        tip="Receive an email one week and one day in advance of an unfinished deadline"
                    />
                </h2>
            </div>
            <div
                v-for="preference in preferences"
                :key="preference['key']"
                class="clearfix mt-2"
            >
                <radio-button
                    v-model="$store.getters['preferences/saved'][preference['key']]"
                    :options="[
                        {
                            value: 'p',
                            icon: 'bell',
                            class: 'add-button',
                        },
                        {
                            value: 'd',
                            icon: 'clock',
                            class: 'add-button',
                        },
                        {
                            value: 'w',
                            icon: 'calendar',
                            class: 'add-button',
                        },
                        {
                            value: 'o',
                            icon: 'times',
                            class: 'delete-button',
                        },
                    ]"
                    class="float-right"
                    @input="e => changePreference(preference['key'], e)"
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
import RadioButton from '@/components/assets/RadioButton.vue'
import tooltip from '@/components/assets/Tooltip.vue'

export default {
    components: {
        RadioButton,
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
                    name: 'Journal updates',
                    key: 'new_node_notifications',
                    tooltip: 'Receive an email when a new deadline is added to your journal.',
                },
                {
                    name: 'New entry',
                    key: 'new_entry_notifications',
                    tooltip: 'Receive an email when a new entry is posted.',
                },
                {
                    name: 'Grade updates',
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
