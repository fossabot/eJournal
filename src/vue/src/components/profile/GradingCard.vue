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
                :isActive="$store.getters['preferences/autoSelectUngradedEntry']"
                class="float-right"
                @parentActive="getAutoSelectUngradedEntry"
            />
            <h2 class="theme-h2 field-heading multi-form">
                Auto-select first ungraded entry
            </h2>
            Upon viewing a journal or submitting a grade, automatically select the first ungraded entry
            <hr/>
            <toggle-switch
                :isActive="$store.getters['preferences/autoProceedNextJournal']"
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
import preferencesAPI from '@/api/preferences.js'

export default {
    components: {
        toggleSwitch,
    },
    props: ['userData'],
    methods: {
        getAutoSelectUngradedEntry (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { auto_select_ungraded_entry: isActive },
                { customSuccessToast: 'Entry grading setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit(
                        'preferences/SET_AUTO_SELECT_UNGRADED_ENTRY', preferences.auto_select_ungraded_entry)
                })
        },
        getAutoProceedNextJournal (isActive) {
            preferencesAPI.update(
                this.$store.getters['user/uID'],
                { auto_proceed_next_journal: isActive },
                { customSuccessToast: 'Journal grading setting updated successfully.' },
            )
                .then((preferences) => {
                    this.$store.commit(
                        'preferences/SET_AUTO_PROCEED_NEXT_JOURNAL', preferences.auto_proceed_next_journal)
                })
        },
    },
}
</script>
