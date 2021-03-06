<!-- TODO Is this check really required if we redirect, or even better have correct flow anyway? -->
<template v-if="$hasPermission('can_view_all_journals')">
    <content-columns>
        <bread-crumb
            slot="main-content-column"
            @edit-click="handleEdit()"
        />
        <b-alert
            v-if="LTILeftJournal"
            slot="main-content-column"
            show
            dismissible
        >
            <b>Warning:</b> The author of the submission you viewed in the LMS (Canvas) is no longer a member of any
            journal for this assignment.
        </b-alert>

        <div slot="main-content-column">
            <input
                v-model="searchValue"
                class="theme-input full-width multi-form"
                type="text"
                placeholder="Search..."
            />

            <div class="d-flex">
                <theme-select
                    v-model="journalGroupFilter"
                    label="name"
                    trackBy="name"
                    :options="groups"
                    :multiple="true"
                    :searchable="true"
                    :multiSelectText="`active group filter${journalGroupFilter &&
                        journalGroupFilter.length === 1 ? '' : 's'}`"
                    placeholder="Filter By Group"
                    class="multi-form mr-2"
                />
                <b-form-select
                    v-model="selectedSortOption"
                    :selectSize="1"
                    class="theme-select multi-form mr-2"
                >
                    <option value="name">
                        Sort by name
                    </option>
                    <option value="username">
                        Sort by username
                    </option>
                    <option value="markingNeeded">
                        Sort by marking needed
                    </option>
                    <option value="points">
                        Sort by points
                    </option>
                </b-form-select>
                <b-button
                    v-if="!order"
                    class="multi-form"
                    @click.stop
                    @click="toggleOrder(!order)"
                >
                    <icon name="long-arrow-alt-down"/>
                    Ascending
                </b-button>
                <b-button
                    v-if="order"
                    class="multi-form"
                    @click.stop
                    @click="toggleOrder(!order)"
                >
                    <icon name="long-arrow-alt-up"/>
                    Descending
                </b-button>
            </div>

            <div class="d-flex flex-wrap assignments-menu-wrapper-margin">
                <b-button
                    v-if="$hasPermission('can_publish_grades') && assignmentJournals && assignmentJournals.length > 0"
                    class="add-button multi-form fill-form-width"
                    @click="publishGradesAssignment"
                >
                    <icon name="upload"/>
                    {{ assignment.journals.length === filteredJournals.length ?
                        "Publish all grades" : "Publish grades" }}
                </b-button>
                <b-button
                    v-if="$hasPermission('can_edit_assignment') && assignment.lti_courses
                        && Object.keys(assignment.lti_courses).length > 1"
                    class="add-button multi-form fill-form-width"
                    @click="showModal('manageLTIModal')"
                >
                    <icon name="graduation-cap"/>
                    Manage LTI
                </b-button>
                <b-button
                    v-if="$hasPermission('can_publish_grades') && assignmentJournals.length > 0"
                    class="change-button multi-form fill-form-width"
                    @click="showModal('bonusPointsModal')"
                >
                    <icon name="star"/>
                    Import bonus points
                </b-button>
                <b-button
                    v-if="assignmentJournals.length > 0"
                    class="add-button multi-form fill-form-width"
                    @click="showModal('assignmentExportSpreadsheetModal')"
                >
                    <icon name="file-export"/>
                    Export results
                </b-button>
            </div>

            <b-modal
                ref="bonusPointsModal"
                title="Import bonus points"
                size="lg"
                hideFooter
                noEnforceFocus
                @hide="$refs['bounsPointsUpload'].resetErrorLogs()"
            >
                <b-card class="no-hover">
                    <h2 class="theme-h2 multi-form">
                        Add bonus points to multiple journals at once
                    </h2>
                    Use the button below to import bonus points from a <i>comma separated value</i> file (.csv).
                    This type of file can be easily generated by any spreadsheet application. Use the following
                    format:<br/>

                    <div class="text-monospace multi-form full-width text-center">
                        username1, bonus1<br/>
                        username2, bonus2<br/>
                        username3, bonus3<br/>
                    </div>

                    <b>Note:</b> Importing bonus points for a user will overwrite their current bonus points!
                    <hr/>

                    <bonus-file-upload-input
                        ref="bounsPointsUpload"
                        :acceptedFiletype="'*/*.csv'"
                        :maxSizeBytes="$root.maxFileSizeBytes"
                        :endpoint="'assignments/' + $route.params.aID + '/add_bonus_points'"
                        :aID="$route.params.aID"
                        class="mt-2"
                        @bonusPointsSuccesfullyUpdated="hideModal('bonusPointsModal'); init()"
                    />
                </b-card>
            </b-modal>

            <b-modal
                ref="assignmentExportSpreadsheetModal"
                title="Export to spreadsheet"
                size="lg"
                hideFooter
                noEnforceFocus
            >
                <b-card class="no-hover">
                    <h2 class="theme-h2 multi-form">
                        Export assignment results
                    </h2>
                    Select which columns should be included in the exported file.
                    <hr/>
                    <assignment-spreadsheet-export
                        :assignment="assignment"
                        :filteredJournals="filteredJournals"
                        :assignmentJournals="assignmentJournals"
                        @spreadsheet-exported="hideModal('assignmentExportSpreadsheetModal')"
                    />
                </b-card>
            </b-modal>

            <b-modal
                v-if="$hasPermission('can_edit_assignment') && assignment.lti_courses
                    && Object.keys(assignment.lti_courses).length > 1"
                ref="manageLTIModal"
                title="Manage LTI"
                size="lg"
                hideFooter
                noEnforceFocus
                @show="newActiveLTICourse = assignment.active_lti_course.cID"
                @hide="newActiveLTICourse = null"
            >
                <b-card class="no-hover">
                    <h2 class="theme-h2">
                        Select active course
                    </h2>
                    This assignment is linked to multiple courses on your LMS.
                    Grades can only be passed back to one course at a time.
                    Select from the options below which course should be used for grade passback.<br/>
                    <hr/>
                    <b-form-select
                        v-model="newActiveLTICourse"
                        class="theme-select full-width mt-2 mb-2"
                    >
                        <option
                            v-for="(name, id) in assignment.lti_courses"
                            :key="`lti-option-${cID}-${id}`"
                            :value="parseInt(id)"
                        >
                            {{ name }}
                        </option>
                    </b-form-select>

                    <b class="text-red">Warning:</b> After changing this option, students will not be
                    able to update their journals for this assignment until they visit the assignment
                    on your LMS at least once.<br/>
                    <hr/>
                    <b-button
                        class="add-button d-block float-right"
                        :class="{'input-disabled': assignment.active_lti_course.cID === newActiveLTICourse}"
                        @click="saveNewActiveLTICourse"
                    >
                        <icon name="save"/>
                        Save
                    </b-button>
                </b-card>
            </b-modal>
        </div>

        <load-wrapper
            slot="main-content-column"
            :loading="loadingJournals"
        >
            <div
                v-for="journal in filteredJournals"
                :key="journal.id"
            >
                <journal-card
                    :journal="journal"
                    :assignment="assignment"
                    @click.native="$router.push({
                        name: 'Journal',
                        params: {
                            cID: $route.params.cID,
                            aID: assignment.id,
                            jID: journal.id
                        }
                    })"
                    @journal-deleted="journalDeleted(journal)"
                />
            </div>
            <main-card
                v-if="assignmentJournals.length === 0"
                line1="No journals for this assignment"
                :line2="assignment.is_group_assignment ? 'Create journals by using the button below.' :
                    'No participants with a journal'"
                class="no-hover border-dark-grey"
            />
            <main-card
                v-else-if="filteredJournals.length === 0"
                line1="No journals found"
                line2="There are no journals that match your search query."
                class="no-hover border-dark-grey"
            />
            <b-button
                v-if="$hasPermission('can_manage_journals') && assignment.is_group_assignment"
                class="multi-form add-button"
                @click="showModal('createJournalModal')"
            >
                <icon name="plus"/>
                Create new journals
            </b-button>

            <b-modal
                v-if="$hasPermission('can_manage_journals') && assignment.is_group_assignment"
                ref="createJournalModal"
                title="Create new journals"
                size="lg"
                hideFooter
                @show="resetNewJournals"
            >
                <b-card class="no-hover">
                    <b-form @submit.prevent="createNewJournals">
                        <h2 class="theme-h2 field-heading multi-form">
                            Name
                        </h2>
                        <b-input
                            v-model="newJournalName"
                            placeholder="Journal"
                            class="theme-input multi-form"
                        />
                        <h2 class="theme-h2 field-heading">
                            Member limit
                        </h2>
                        <b-input
                            v-model="newJournalMemberLimit"
                            type="number"
                            placeholder="No member limit"
                            min="2"
                            class="theme-input multi-form"
                        />

                        <b-button
                            v-if="!repeatCreateJournal"
                            class="multi-form mr-3"
                            @click="repeatCreateJournal = true"
                        >
                            <icon name="book"/>
                            Create multiple journals
                        </b-button>
                        <b-button
                            v-else
                            class="multi-form mr-3"
                            @click="repeatCreateJournal = false"
                        >
                            <icon name="book"/>
                            Create single journal
                        </b-button>

                        <div
                            v-if="repeatCreateJournal"
                            class="shift-deadlines-input"
                        >
                            <icon
                                v-b-tooltip:hover="'All journals created will be numbered sequentially'"
                                name="info-circle"
                            />
                            Repeat
                            <b-form-input
                                v-model="newJournalCount"
                                type="number"
                                min="2"
                                class="theme-input"
                                required
                            />
                            times
                        </div>

                        <b-button
                            type="submit"
                            class="add-button d-block float-right"
                            :class="{'input-disabled': newJournalRequestInFlight}"
                        >
                            <icon name="plus-square"/>
                            Create
                        </b-button>
                    </b-form>
                </b-card>
            </b-modal>
        </load-wrapper>

        <div
            v-if="stats"
            slot="right-content-column"
        >
            <h3 class="theme-h3">
                Insights
            </h3>
            <statistics-card :stats="stats"/>
        </div>
    </content-columns>
</template>

<script>
import assignmentSpreadsheetExport from '@/components/assignment/AssignmentSpreadsheetExport.vue'
import bonusFileUploadInput from '@/components/assets/file_handling/BonusFileUploadInput.vue'
import breadCrumb from '@/components/assets/BreadCrumb.vue'
import contentColumns from '@/components/columns/ContentColumns.vue'
import loadWrapper from '@/components/loading/LoadWrapper.vue'
import mainCard from '@/components/assets/MainCard.vue'
import statisticsCard from '@/components/assignment/StatisticsCard.vue'
import journalCard from '@/components/assignment/JournalCard.vue'

import store from '@/Store.vue'
import assignmentAPI from '@/api/assignment.js'
import groupAPI from '@/api/group.js'
import gradeAPI from '@/api/grade.js'
import participationAPI from '@/api/participation.js'
import journalAPI from '@/api/journal.js'
import { mapGetters, mapMutations } from 'vuex'

export default {
    name: 'Assignment',
    components: {
        assignmentSpreadsheetExport,
        bonusFileUploadInput,
        breadCrumb,
        contentColumns,
        loadWrapper,
        mainCard,
        statisticsCard,
        journalCard,
    },
    props: {
        cID: {
            required: true,
        },
        aID: {
            required: true,
        },
    },
    data () {
        return {
            assignment: {},
            assignmentJournals: [],
            stats: null,
            groups: [],
            loadingJournals: true,
            newActiveLTICourse: null,
            filteredGroups: null,
            newJournalName: null,
            newJournalMemberLimit: null,
            repeatCreateJournal: false,
            newJournalCount: null,
            newJournalRequestInFlight: false,
            LTILeftJournal: false,
        }
    },
    computed: {
        ...mapGetters({
            journalSortBy: 'preferences/journalSortBy',
            isSuperuser: 'user/isSuperuser',
            order: 'preferences/journalSortAscending',
            getJournalSearchValue: 'preferences/journalSearchValue',
            getJournalGroupFilter: 'preferences/journalGroupFilter',
            getSelfSetGroupFilter: 'preferences/journalSelfSetGroupFilter',
        }),
        journalGroupFilter: {
            get () {
                return this.getJournalGroupFilter
            },
            set (value) {
                this.setJournalGroupFilter(value)
                this.setSelfSetGroupFilter(true)
            },
        },
        searchValue: {
            get () {
                return this.getJournalSearchValue
            },
            set (value) {
                this.setJournalSearchValue(value)
            },
        },
        selectedSortOption: {
            get () {
                return this.journalSortBy
            },
            set (value) {
                this.setJournalSortBy(value)
            },
        },
        filteredJournals () {
            store.setFilteredJournals(this.assignmentJournals, this.order, this.journalGroupFilter,
                this.getJournalSearchValue, this.journalSortBy)
            this.calcStats(store.state.filteredJournals)
            return store.state.filteredJournals
        },
    },
    created () {
        // TODO Should be moved to the breadcrumb, ensuring there is no more natural flow left that can get you to this
        // page without manipulating the url manually. If someone does this, simply let the error be thrown
        // (no checks required)
        if (!this.$hasPermission('can_view_all_journals', 'assignment', String(this.aID))) {
            if (this.$root.previousPage) {
                this.$router.push({ name: this.$root.previousPage.name, params: this.$root.previousPage.params })
            } else {
                this.$router.push({ name: 'Home' })
            }
            return
        }

        /* Check query to see if the LTI submission corresponds to a left journal. Remove query param to prevent
         * showing an alert on subsequent page visits / refreshes. */
        if (this.$route.query.left_journal) {
            const query = Object.assign({}, this.$route.query)
            delete query.left_journal
            this.$router.replace({ query })
            this.LTILeftJournal = true
        }

        this.init()
    },
    methods: {
        ...mapMutations({
            setJournalSortBy: 'preferences/SET_JOURNAL_SORT_BY',
            toggleOrder: 'preferences/SET_JOURNAL_SORT_ASCENDING',
            setJournalSearchValue: 'preferences/SET_JOURNAL_SEARCH_VALUE',
            setJournalGroupFilter: 'preferences/SET_JOURNAL_GROUP_FILTER',
            switchJournalAssignment: 'preferences/SWITCH_JOURNAL_ASSIGNMENT',
            setSelfSetGroupFilter: 'preferences/SET_JOURNAL_SELF_SET_GROUP_FILTER',
        }),
        init () {
            this.switchJournalAssignment(this.aID)

            const initialCalls = []
            initialCalls.push(assignmentAPI.get(this.aID, this.cID))
            initialCalls.push(groupAPI.getFromAssignment(this.cID, this.aID))
            /* Superuser does not have any participation, this should not redict to error, nor give an error toast */
            if (!this.isSuperuser) {
                initialCalls.push(participationAPI.get(this.cID))
            }

            Promise.all(initialCalls).then((results) => {
                this.loadingJournals = false
                this.assignment = results[0]
                this.assignmentJournals = results[0].journals
                this.groups = results[1].sort((a, b) => b.name < a.name)
                if (!this.isSuperuser) {
                    const participant = results[2]
                    /* If the group filter has not been set, set it to the
                       groups of the user provided that yields journals. */
                    if (!this.getSelfSetGroupFilter && participant && participant.groups) {
                        this.setJournalGroupFilter(participant.groups.filter(
                            participantGroup => this.groups.some(group => group.id === participantGroup.id)))
                    }
                }

                /* If there are no groups or the current group filter yields no journals, remove the filter. */
                if (!this.groups || this.filteredJournals.length === 0) {
                    this.setJournalGroupFilter(null)
                }
            })
        },
        showModal (ref) {
            this.$refs[ref].show()
        },
        hideModal (ref) {
            this.$refs[ref].hide()
        },
        handleEdit () {
            this.$router.push({
                name: 'FormatEdit',
                params: {
                    cID: this.cID,
                    aID: this.aID,
                },
            })
        },
        publishGradesAssignment () {
            if (this.assignment.journals.length === store.state.filteredJournals.length) {
                if (window.confirm('Are you sure you want to publish the grades for all journals?')) {
                    gradeAPI.publish_all_assignment_grades(this.aID, {
                        customErrorToast: 'Error while publishing all grades for this assignment.',
                        customSuccessToast: 'Published all grades for this assignment.',
                    }).then(() => {
                        assignmentAPI.get(this.aID, this.cID)
                            .then((assignment) => {
                                this.assignmentJournals = assignment.journals
                                this.stats = assignment.stats
                            })
                    })
                }
            } else if (window.confirm('Are you sure you want to publish the grades of the filtered journals?')) {
                const allJournals = []
                this.filteredJournals.forEach((journal) => {
                    allJournals.push(journalAPI.update(journal.id, { published: true }, {
                        customErrorToast: `Error while publishing grades for ${journal.name}.`,
                    }))
                })
                Promise.all(allJournals).then(() => {
                    this.$toasted.success('Published grades.')
                    assignmentAPI.get(this.aID, this.cID)
                        .then((assignment) => {
                            this.assignmentJournals = assignment.journals
                            this.stats = assignment.stats
                        })
                })
            }
        },
        saveNewActiveLTICourse () {
            if (window.confirm('Are you sure you want to change the active LTI course for grade passback?'
                + ' Students will not be able to update their journals for this assignment until they visit'
                + ' the assignment on your LMS at least once.')) {
                assignmentAPI.update(this.aID, {
                    active_lti_course: this.newActiveLTICourse,
                })
                    .then(() => {
                        this.$toasted.success('Updated active LTI course')
                        this.$refs.manageLTIModal.hide()
                    })
            }
        },
        calcStats (filteredJournals) {
            let needsMarking = 0
            let unpublished = 0
            let points = 0

            for (let i = 0; i < filteredJournals.length; i++) {
                needsMarking += filteredJournals[i].needs_marking
                unpublished += filteredJournals[i].unpublished
                points += filteredJournals[i].grade
            }
            this.stats = {
                needsMarking,
                unpublished,
                averagePoints: points / filteredJournals.length,
            }
        },
        resetNewJournals () {
            this.newJournalName = null
            this.newJournalMemberLimit = null
            this.repeatCreateJournal = false
            this.newJournalCount = null
        },
        createNewJournals () {
            this.newJournalRequestInFlight = true
            if (!this.newJournalCount) {
                this.newJournalCount = 1
            }
            journalAPI.create({
                name: this.newJournalName,
                amount: this.newJournalCount,
                author_limit: this.newJournalMemberLimit > 1 ? this.newJournalMemberLimit : 0,
                assignment_id: this.assignment.id,
            })
                .then((journals) => {
                    this.assignment.journals = journals
                    this.assignmentJournals = journals
                    this.hideModal('createJournalModal')
                    this.newJournalRequestInFlight = false
                })
                .catch(() => { this.newJournalRequestInFlight = false })
        },
        journalDeleted (journal) {
            this.assignment.journals.splice(this.assignment.journals.indexOf(journal), 1)
            this.assignmentJournals = this.assignment.journals
        },
    },
}
</script>

<style lang="sass">
.create-journals-repeat
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

.assignments-menu-wrapper-margin
    margin: 0px -4px
</style>
