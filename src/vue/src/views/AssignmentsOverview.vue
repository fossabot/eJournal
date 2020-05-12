<template>
    <content-single-column>
        <div
            v-if="$root.canGradeForSomeCourse"
            class="text-grey float-right unselectable cursor-pointer"
        >
            <span
                v-if="selectedFilterOwnGroups"
                v-b-tooltip.hover
                title="Only showing to do items for groups which you are a member of"
                @click="selectedFilterOwnGroups = false"
            >
                Showing to do:
                <b>own groups</b>
            </span>
            <span
                v-else
                v-b-tooltip.hover
                title="Showing to do items for all groups"
                @click="selectedFilterOwnGroups = true"
            >
                Showing to do:
                <b>all</b>
            </span>
        </div>
        <bread-crumb :currentPage="'Assignments'"/>
        <input
            v-model="searchValue"
            class="theme-input full-width multi-form"
            type="text"
            placeholder="Search..."
        />
        <div class="d-flex">
            <b-form-select
                v-model="selectedSortOption"
                :selectSize="1"
                class="theme-select multi-form mr-2"
            >
                <option value="date">
                    Sort by date
                </option>
                <option value="name">
                    Sort by name
                </option>
                <option
                    v-if="$root.canGradeForSomeCourse"
                    value="markingNeeded"
                >
                    Sort by marking needed
                </option>
            </b-form-select>
            <b-button
                v-if="!order"
                class="button multi-form"
                @click.stop
                @click="setOrder(!order)"
            >
                <icon name="long-arrow-alt-down"/>
                Ascending
            </b-button>
            <b-button
                v-if="order"
                class="button multi-form"
                @click.stop
                @click="setOrder(!order)"
            >
                <icon name="long-arrow-alt-up"/>
                Descending
            </b-button>
        </div>
        <load-wrapper :loading="loadingAssignments">
            <div
                v-for="(d, i) in computedAssignments"
                :key="i"
            >
                <b-link
                    v-if="d.course"
                    :to="$root.assignmentRoute(d)"
                    tag="b-button"
                >
                    <todo-card
                        :deadline="d"
                        :course="d.course"
                        :filterOwnGroups="selectedFilterOwnGroups"
                    />
                </b-link>
                <b-link
                    v-for="(course, j) in d.courses"
                    v-else
                    :key="`${i}-${j}`"
                    :to="$root.assignmentRoute(d, course)"
                    tag="b-button"
                >
                    <todo-card
                        :deadline="d"
                        :course="course"
                        :filterOwnGroups="selectedFilterOwnGroups"
                    />
                </b-link>
            </div>
            <main-card
                v-if="computedAssignments.length === 0"
                line1="No assignments found"
                line2="You currently do not participate in any assignments."
                class="no-hover border-dark-grey"
            />
        </load-wrapper>
    </content-single-column>
</template>

<script>
import contentSingleColumn from '@/components/columns/ContentSingleColumn.vue'
import breadCrumb from '@/components/assets/BreadCrumb.vue'
import loadWrapper from '@/components/loading/LoadWrapper.vue'
import todoCard from '@/components/assets/TodoCard.vue'
import mainCard from '@/components/assets/MainCard.vue'
import assignmentAPI from '@/api/assignment.js'

import { mapGetters, mapMutations } from 'vuex'

export default {
    name: 'AssignmentsOverview',
    components: {
        contentSingleColumn,
        breadCrumb,
        loadWrapper,
        todoCard,
        mainCard,
    },
    data () {
        return {
            deadlines: [],
            loadingAssignments: true,
        }
    },
    computed: {
        ...mapGetters({
            order: 'preferences/assignmentOverviewSortAscending',
            getAssignmentSearchValue: 'preferences/assignmentOverviewSearchValue',
            getAssignmentOverviewSortBy: 'preferences/assignmentOverviewSortBy',
            getAssignmentOverviewFilterOwnGroups: 'preferences/assignmentOverviewFilterOwnGroups',
        }),
        searchValue: {
            get () {
                return this.getAssignmentSearchValue
            },
            set (value) {
                this.setAssignmentSearchValue(value)
            },
        },
        selectedSortOption: {
            get () {
                return this.getAssignmentOverviewSortBy
            },
            set (value) {
                this.setAssignmentOverviewSortBy(value)
            },
        },
        selectedFilterOwnGroups: {
            get () {
                return this.getAssignmentOverviewFilterOwnGroups
            },
            set (value) {
                this.setAssignmentOverviewOwnGroups(value)
            },
        },
        computedAssignments () {
            const self = this

            function compareName (a, b) {
                return b.name < a.name
            }

            function compareDate (a, b) {
                if (!a.deadline.date) { return 1 }
                if (!b.deadline.date) { return -1 }
                return new Date(a.deadline.date) - new Date(b.deadline.date)
            }

            function compareMarkingNeeded (a, b) {
                return (a.stats.needs_marking + a.stats.unpublished) - (b.stats.needs_marking + b.stats.unpublished)
            }

            function searchFilter (assignment) {
                return assignment.name.toLowerCase().includes(self.getAssignmentSearchValue.toLowerCase())
            }

            const deadlines = this.deadlines.filter(searchFilter)
            if (this.selectedSortOption === 'name') {
                deadlines.sort(compareName)
            } else if (this.selectedSortOption === 'date') {
                deadlines.sort(compareDate)
            } else if (this.selectedSortOption === 'markingNeeded') {
                deadlines.sort(compareMarkingNeeded)
            }

            return this.order ? deadlines.reverse() : deadlines
        },
    },
    created () {
        assignmentAPI.list()
            .then((deadlines) => {
                this.deadlines = deadlines
                this.loadingAssignments = false
            })
    },
    methods: {
        ...mapMutations({
            setOrder: 'preferences/SET_ASSIGNMENT_OVERVIEW_SORT_ASCENDING',
            setAssignmentSearchValue: 'preferences/SET_ASSIGNMENT_OVERVIEW_SEARCH_VALUE',
            setAssignmentOverviewSortBy: 'preferences/SET_ASSIGNMENT_OVERVIEW_SORT_BY',
            setAssignmentOverviewOwnGroups: 'preferences/SET_ASSIGNMENT_OVERVIEW_FILTER_OWN_GROUPS',
        }),
        compare (a, b) {
            if (a < b) { return this.order ? 1 : -1 }
            if (a > b) { return this.order ? -1 : 1 }
            return 0
        },
    },
}
</script>
