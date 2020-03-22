<template>
    <div>
        <div
            v-for="linkable in linkableAssignments"
            :key="`linkable-${linkable.course.id}`"
        >
            <main-card
                v-if="linkable.assignments.length > 0"
                :key="`course-${linkable.course.id}-import`"
                :line1="linkable.course.name"
                :line2="linkable.course.startdate ? (linkable.course.startdate.substring(0, 4) +
                    (linkable.course.enddate ? ` - ${linkable.course.enddate.substring(0, 4)}` : '')) : ''"
                @click.native="() => {
                    selectedCourse = linkable.course.id
                }"
            />
            <div
                v-if="selectedCourse === linkable.course.id"
                class="pl-5"
            >
                <assignment-card
                    v-for="assignment in linkable.assignments"
                    :key="`assignment-${assignment.id}-import`"
                    :assignment="assignment"
                    @click.native="linkAssignment(assignment.id, assignment.lti_count)"
                />
            </div>
        </div>
    </div>
</template>

<script>
import assignmentCard from '@/components/assignment/AssignmentCard.vue'
import mainCard from '@/components/assets/MainCard.vue'
import assignmentAPI from '@/api/assignment.js'

export default {
    name: 'LinkAssignment',
    components: {
        assignmentCard,
        mainCard,
    },
    props: ['lti', 'page', 'linkableAssignments'],
    data () {
        return {
            selectedCourse: null,
        }
    },
    methods: {
        linkAssignment (aID, ltiCount) {
            if (!ltiCount || window.confirm(
                `This assignment is already linked to ${ltiCount > 1 ? `${ltiCount} ` : 'an'}`
                + `other assignment${ltiCount > 1 ? 's' : ''} on the LMS (Canvas). Are you sure you want to`
                + ' link this one as well? Grades will only be passed back to the new link.')) {
                assignmentAPI.update(aID, {
                    lti_id: this.lti.ltiAssignID,
                    points_possible: this.lti.ltiPointsPossible,
                    is_published: this.lti.ltiAssignPublished,
                    unlock_date: this.lti.ltiAssignUnlock ? this.lti.ltiAssignUnlock.slice(0, -6) : null,
                    due_date: this.lti.ltiAssignDue ? this.lti.ltiAssignDue.slice(0, -6) : null,
                    lock_date: this.lti.ltiAssignLock ? this.lti.ltiAssignLock.slice(0, -6) : null,
                    course_id: this.page.cID,
                })
                    .then((assignment) => { this.$emit('handleAction', assignment.id) })
                    .catch((error) => {
                        if (error.response.status === 400
                            && error.response.data.description.startsWith(
                                'You cannot unpublish an assignment that already has submissions')) {
                            this.$toasted.error(
                                `We are sorry, the assignment is unpublished on Canvas but holds published entries on
                                eJournal. We cannot unpublish these published entries.
                                Publish the Canvas assignment, and try again with a fresh launch from Canvas.`,
                                { duration: 12000 },
                            )
                        }
                    })
            }
        },
    },
}
</script>
