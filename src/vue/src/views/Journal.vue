<template>
    <div v-if="isOwn !== null">
        <journal-student
            v-if="isOwn"
            ref="journal-student-ref"
            :cID="cID"
            :aID="aID"
            :jID="jID"
        />
        <journal-non-student
            v-else
            ref="journal-non-student-ref"
            :cID="cID"
            :aID="aID"
            :jID="jID"
        />
    </div>
</template>

<script>
import journalStudent from '@/components/journal/JournalStudent.vue'
import journalNonStudent from '@/components/journal/JournalNonStudent.vue'
import journalAPI from '@/api/journal.js'

export default {
    name: 'Journal',
    components: {
        journalStudent,
        journalNonStudent,
    },
    props: ['cID', 'aID', 'jID'],
    data () {
        return {
            isOwn: null,
        }
    },
    created () {
        journalAPI.isOwnJournal(this.jID).then((isOwn) => {
            this.isOwn = isOwn
        })
    },
    beforeRouteLeave (to, from, next) {
        // TODO: change to authon in journal
        if (this.isOwn && !this.$refs['journal-student-ref'].discardChanges()) {
            next(false)
        } else if (this.isOwn === false && !this.$refs['journal-non-student-ref'].discardChanges()) {
            next(false)
        } else {
            next()
        }
    },
}
</script>

<style lang="sass">
@import '~sass/partials/timeline-page-layout.sass'
</style>
