<template>
    <b-card
        :class="$root.getBorderClass(journal.id)"
        class="journal-card"
    >
        <b-row noGutters>
            <b-col
                class="d-flex"
                :md="$hasPermission('can_view_all_journals') ? 7 : 12"
            >
                <div class="portrait-wrapper">
                    <img
                        class="no-hover"
                        :src="journal.image"
                    />
                    <number-badge
                        v-if="$hasPermission('can_view_all_journals') && markingNeeded + unpublished > 0"
                        :leftNum="markingNeeded"
                        :rightNum="unpublished"
                        :title="squareInfo"
                    />
                </div>
                <div class="student-details">
                    <b
                        class="max-one-line"
                        :title="journal.name"
                    >
                        {{ journal.name }}
                    </b>
                    <span
                        class="max-one-line shift-up-4"
                        :title="journalAuthors"
                    >
                        <b-badge
                            v-if="journal.author_limit > 1"
                            v-b-tooltip:hover="`This journal currently has ${ journal.authors.length } of max `
                                + `${ journal.author_limit } members`"
                            class="text-white mr-1"
                        >
                            {{ journal.authors.length }}/{{ journal.author_limit }}
                        </b-badge>
                        <b-badge
                            v-if="journal.author_limit === 0"
                            v-b-tooltip:hover="`This journal currently has ${ journal.authors.length } members `
                                + 'and no member limit'"
                            class="text-white mr-1"
                        >
                            {{ journal.authors.length }}
                        </b-badge>
                        <b-badge
                            v-if="journal.locked"
                            class="background-red"
                        >
                            <icon
                                v-b-tooltip:hover="
                                    'Members are locked: it is not possible to join or leave this journal'"
                                name="lock"
                                class="fill-white"
                                scale="0.65"
                            />
                        </b-badge>
                        <span v-if="!assignment.is_group_assignment || !expanded">
                            {{ journalAuthors }}
                        </span>
                    </span>
                </div>
            </b-col>
            <b-col
                v-if="$hasPermission('can_view_all_journals')"
                class="mt-2"
                md="5"
            >
                <progress-bar
                    :currentPoints="journal.stats.acquired_points"
                    :totalPoints="assignment.points_possible"
                />
            </b-col>
        </b-row>
        <slot/>
        <div
            v-if="assignment.is_group_assignment && $hasPermission('can_manage_journals')"
            class="expand-controls full-width text-center"
            @click.prevent.stop="expanded = !expanded"
        >
            <icon
                :name="expanded ? 'caret-up' : 'caret-down'"
                class="fill-grey"
            />
        </div>
        <div
            v-if="expanded"
            class="mt-3 mb-4"
            @click.prevent.stop=""
        >
            <journal-members
                v-if="assignment.is_group_assignment"
                :journal="journal"
                :assignment="assignment"
            />
        </div>
    </b-card>
</template>

<script>
import progressBar from '@/components/assets/ProgressBar.vue'
import numberBadge from '@/components/assets/NumberBadge.vue'
import journalMembers from '@/components/journal/JournalMembers.vue'

export default {
    components: {
        progressBar,
        numberBadge,
        journalMembers,
    },
    props: {
        assignment: {
            required: true,
        },
        journal: {
            required: true,
        },
    },
    data () {
        return {
            expanded: false,
        }
    },
    computed: {
        numMarkingNeeded () {
            return this.journal.stats ? this.journal.stats.submitted - this.journal.stats.graded : 0
        },
        journalAuthors () {
            if (this.assignment.is_group_assignment) {
                return this.journal.authors.map(a => a.user.full_name).join(', ')
            }

            return this.journal.authors.map(a => a.user.username).join(', ')
        },
        groups () {
            const groups = []
            this.journal.authors.forEach((student) => {
                if (student.user.groups) {
                    student.user.groups.forEach((group) => {
                        if (!groups.includes(group)) {
                            groups.push(group.name)
                        }
                    })
                }
            })
            return groups.join(', ')
        },
        markingNeeded () {
            return this.journal.stats ? this.journal.stats.submitted - this.journal.stats.graded : 0
        },
        unpublished () {
            return this.journal.stats ? this.journal.stats.graded - this.journal.stats.published : 0
        },
        squareInfo () {
            const info = []
            if (this.markingNeeded === 1) {
                info.push('an entry needs marking')
            } else if (this.markingNeeded > 1) {
                info.push(`${this.markingNeeded} entries need marking`)
            }
            if (this.unpublished === 1) {
                info.push('an entry needs to be published')
            } else if (this.unpublished > 1) {
                info.push(`${this.unpublished} grades need to be published`)
            }
            const s = info.join(' and ')
            return `${s.charAt(0).toUpperCase()}${s.slice(1)}`
        },
        canManageJournal () {
            return this.assignment.is_group_assignment && (this.assignment.can_set_journal_name
                || this.assignment.can_set_journal_image || this.$hasPermission('can_manage_journals'))
        },
    },
    methods: {
        journalDeleted () {
            this.$emit('journal-deleted')
        },
    },
}
</script>

<style lang="sass">
@import '~sass/partials/shadows.sass'
@import '~sass/modules/breakpoints.sass'
@import '~sass/modules/colors.sass'

.journal-card
    .portrait-wrapper
        position: relative
        min-width: 80px
        height: 70px
        img
            @extend .shadow
            width: 70px
            height: 70px
            border-radius: 50% !important
        .number-badge
            position: absolute
            right: 0px
            top: 0px
    .student-details
        position: relative
        width: calc(100% - 80px)
        min-height: 70px
        flex-direction: column
        padding: 10px
        .max-one-line
            display: block
            width: 100%
            text-overflow: ellipsis
            white-space: nowrap
            overflow: hidden
        &.list-view
            padding-left: 40px
        @include sm-max
            align-items: flex-end
    .default-cursor
        cursor: default
    .expand-controls
        position: absolute
        bottom: 0px
        left: 0px
</style>
