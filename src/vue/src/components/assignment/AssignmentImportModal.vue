<template>
    <b-modal
        :id="modalID"
        size="lg"
        title="Import assignment"
        hideFooter
        noEnforceFocus
    >
        <b-card class="no-hover">
            <h2 class="theme-h2 multi-form">
                Select an assignment to import
            </h2>
            <p>
                This action will create a new assignment that is identical to the assignment of your choice.
                Existing journals are not imported and will remain accessible only from the original assignment.
            </p>

            <div
                v-for="importable in importableFormats"
                :key="`importable-${importable.course.id}`"
            >
                <main-card
                    :key="`course-${importable.course.id}-import`"
                    :line1="importable.course.name"
                    :line2="importable.course.startdate ? (importable.course.startdate.substring(0, 4) +
                        (importable.course.enddate ? ` - ${importable.course.enddate.substring(0, 4)}` : '')) : ''"
                    @click.native="selectedCourse = importable.course.id"
                />
                <div
                    v-if="selectedCourse === importable.course.id"
                    class="pl-5"
                >
                    <assignment-card
                        v-for="assignment in importable.assignments"
                        :key="`course-${importable.course.id}-assignment-${assignment.id}-import`"
                        :assignment="assignment"
                        :class="{
                            active: selectedAssignment === assignment.id,
                            'no-hover': selectedAssignment === assignment.id,
                        }"
                        @click.native="
                            selectedAssignment = (selectedAssignment !== assignment.id) ? assignment.id : null"
                    />
                </div>
            </div>
            <div v-if="!importableFormats">
                <h4 class="theme-h4">
                    No existing assignments available
                </h4>
                <hr class="m-0 mb-1"/>
                Only assignments where you have permission to edit are available for import.
            </div>

            <div v-if="selectedAssignment !== null">
                <hr/>
                <b-form
                    class="full-width"
                    @submit="importAssignment"
                >
                    <b-button
                        v-if="!shiftImportDates"
                        class="multi-form mr-3"
                        @click="shiftImportDates = true"
                    >
                        <icon name="calendar"/>
                        Shift Deadlines
                    </b-button>
                    <b-button
                        v-else
                        class="multi-form mr-3"
                        @click="shiftImportDates = false"
                    >
                        <icon name="calendar"/>
                        Keep existing deadlines
                    </b-button>

                    <div
                        v-if="shiftImportDates"
                        class="shift-deadlines-input"
                    >
                        <icon
                            v-b-tooltip:hover="'The weekdays of the deadlines will be kept intact'"
                            name="info-circle"
                        />
                        Dates will be shifted by
                        <b-form-input
                            id="months"
                            v-model="months"
                            type="number"
                            class="theme-input"
                        />
                        months
                    </div>

                    <b-button
                        class="add-button float-right"
                        type="submit"
                    >
                        <icon name="file"/>
                        Import
                    </b-button>
                </b-form>
            </div>
        </b-card>
    </b-modal>
</template>

<script>
import assignmentCard from '@/components/assignment/AssignmentCard.vue'
import mainCard from '@/components/assets/MainCard.vue'

import assignmentAPI from '@/api/assignment.js'

export default {
    components: {
        assignmentCard,
        mainCard,
    },
    props: {
        modalID: {
            required: true,
        },
        cID: {
            required: true,
        },
        lti: {
            default: () => ({}),
            required: false,
        },
    },
    data () {
        return {
            selectedCourse: null,
            selectedAssignment: null,
            importableFormats: [],
            assignmentImportInFlight: false,
            shiftImportDates: true,
            months: 0,
        }
    },
    created () {
        assignmentAPI.getImportable()
            .then((data) => {
                this.importableFormats = data
            })
    },
    methods: {
        importAssignment (e) {
            e.preventDefault()

            if (!this.assignmentImportInFlight && this.selectedAssignment) {
                this.assignmentImportInFlight = true
                assignmentAPI.import(this.selectedAssignment, {
                    course_id: this.cID,
                    months_offset: (!this.shiftImportDates || this.months === '') ? 0 : this.months,
                    lti_id: this.lti.ltiAssignID,
                }, { customSuccessToast: 'Assignment succesfully imported.' }).then((response) => {
                    this.assignmentImportInFlight = false

                    this.$store.commit('user/IMPORT_ASSIGNMENT_PERMISSIONS', {
                        sourceAssignmentID: this.selectedAssignment,
                        importAssignmentID: response.assignment_id,
                    })

                    this.$router.push({
                        name: 'FormatEdit',
                        params: {
                            cID: this.cID,
                            aID: response.assignment_id,
                        },
                    })
                }).catch((error) => {
                    this.assignmentImportInFlight = false
                    throw error
                })
            }
        },
    },
}
</script>

<style lang="sass">
.shift-deadlines-input
    font-weight: bold
    color: grey
    margin-bottom: 10px
    display: inline-block
    .theme-input
        display: inline-block
        width: 4em
    svg
        margin-top: -5px
        fill: grey
</style>
