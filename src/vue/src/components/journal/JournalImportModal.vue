<template>
    <b-modal
        :id="modalID"
        :ref="modalID"
        size="lg"
        title="Import journal"
        hideFooter
        noEnforceFocus
    >
        <b-card>
            <h2 class="theme-h2 multi-form">
                Select a journal to import
            </h2>

            <p>
                Please select a journal to import. Your request will be sent to your educator for approval. Once
                approved, the entries of the selected journal will be added to your journal. The reuse of existing
                grades remains at the discretion of your eduator.
            </p>

            <load-wrapper
                :loading="loading"
            >
                <assignment-card
                    v-for="a in assignments"
                    :key="`assignment-${a.id}-preview`"
                    :assignment="a"
                    :uniqueName="!assignments.some(a2 =>
                        a.name === a2.name && a.id !== a2.id
                    )"
                    @click="importJournal(a)"
                />
            </load-wrapper>
        </b-card>
    </b-modal>
</template>

<script>
import assignmentCard from '@/components/assignment/AssignmentCard.vue'
import loadWrapper from '@/components/loading/LoadWrapper.vue'

import assignmentAPI from '@/api/assignment.js'
import courseAPI from '@/api/course.js'

export default {
    components: {
        assignmentCard,
        loadWrapper,
    },
    props: {
        modalID: {
            required: true,
            type: String,
        },
    },
    data () {
        return {
            assignments: [],
            selectedAssignment: null,
            loading: true,
        }
    },
    computed: {
    },
    created () {
        const initCalls = []

        courseAPI.getUserEnrolled()
            .then((courses) => {
                courses.forEach((c) => {
                    console.log(c)
                    initCalls.push(assignmentAPI.list(c.id))
                })

                Promise.all(initCalls).then((results) => {
                    results.forEach((assignments) => {
                        assignments.forEach((a) => {
                            if (a.id !== this.$route.params.aID && !this.assignments.some(a2 => a2.id === a.id)) {
                                this.assignments.push(a)
                            }
                        })
                    })

                    this.loading = false
                })
            })
    },
    methods: {
        importJournal (assignment) {
            if (alert(`Are you sure you want to send a request to import ${assignment.name}`)) {
                // TODO
            }
        },
    },
}
</script>
