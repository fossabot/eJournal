<template>
    <b-card :class="$root.getBorderClass($route.params.cID)">
        <todo-square v-if="checkPermissions() && totalNeedsMarking > 0" :num="totalNeedsMarking" class="float-right" />
        <h6>{{ $root.beautifyDate(deadline) }}</h6>
        <h5>{{ name }}</h5>
        {{ abbr }}
    </b-card>
</template>

<script>
import todoSquare from '@/components/assets/TodoSquare.vue'

export default {
    props: ['deadline', 'name', 'abbr', 'totalNeedsMarking'],
    components: {
        'todo-square': todoSquare
    },
    methods: {
        checkPermissions () {
            if (this.$route.name === 'Course') {
                return this.$root.canViewAssignmentParticipants()
            } else if (this.$route.name === 'AssignmentsOverview' ||
                       this.$route.name === 'Home') {
                return this.$root.canAddCourse()
            }
        }
    }
}
</script>

<style lang="sass" scoped>
@import "~sass/modules/colors.sass"

h6
    display: inline

p
    text-align: right
    font-size: 20px
    color: $theme-blue
    margin-bottom: 0px
</style>