<template>
    <div>
        <h4 class="theme-h4 mb-2 mt-4">
            <span>Grading</span>
        </h4>
        <b-card
            :class="$root.getBorderClass($route.params.uID)"
            class="no-hover multi-form"
        >
            <toggle-switch
                :isActive="$store.getters['preferences/saved'].auto_select_ungraded_entry"
                class="float-right"
                @parentActive="getAutoSelectUngradedEntry"
            />
            <h2 class="theme-h2 field-heading multi-form">
                Auto-select first ungraded entry
            </h2>
            Upon viewing a journal or submitting a grade, automatically select the first ungraded entry
            <hr/>
            <toggle-switch
                :isActive="$store.getters['preferences/saved'].auto_proceed_next_journal"
                class="float-right"
                @parentActive="getAutoProceedNextJournal"
            />
            <h2 class="theme-h2 field-heading">
                Automatically proceed to next journal
            </h2>
            Automatically proceed to the next journal once all entries in a journal are graded
        </b-card>
    </div>
</template>

<script>
import toggleSwitch from '@/components/assets/ToggleSwitch.vue'

export default {
    components: {
        toggleSwitch,
    },
    props: ['userData'],
    methods: {
        getAutoSelectUngradedEntry (isActive) {
            this.$store.commit('preferences/CHANGE_PREFERENCES', { auto_select_ungraded_entry: isActive })
        },
        getAutoProceedNextJournal (isActive) {
            this.$store.commit('preferences/CHANGE_PREFERENCES', { auto_proceed_next_journal: isActive })
        },
    },
}
</script>
