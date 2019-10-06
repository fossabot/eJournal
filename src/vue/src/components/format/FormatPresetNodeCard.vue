<!--
    Editor for the currently selected preset in the format editor.
    Edits the preset prop directly.
    Various (many!) elements emit a changed event to track whether unsaved changes exist.
-->

<template>
    <b-card
        :class="$root.getBorderClass($route.params.cID)"
        class="no-hover overflow-x-hidden"
    >
        <h2
            v-if="!newPreset"
            class="d-inline multi-form"
        >
            <span v-if="currentPreset.type == 'd'">Entry</span>
            <span v-if="currentPreset.type == 'p'">Progress goal</span>
        </h2>

        <b-row v-if="currentPreset.type == 'd'">
            <b-col xl="4">
                <h2 class="field-heading">
                    Unlock date
                    <tooltip tip="Students will be able to work on the entry from this date onwards"/>
                </h2>
                <flat-pickr
                    v-model="currentPreset.unlock_date"
                    class="multi-form theme-input full-width"
                    :config="unlockDateConfig"
                />
            </b-col>
            <b-col xl="4">
                <h2 class="field-heading required">
                    Due date
                    <tooltip
                        tip="Students are expected to have finished their entry by this date, but new entries can
                        still be added until the lock date"
                    />
                </h2>
                <flat-pickr
                    v-model="currentPreset.due_date"
                    class="multi-form theme-input full-width"
                    :config="dueDateConfig"
                    @on-change="$emit('change-due-date')"
                />
            </b-col>
            <b-col xl="4">
                <h2 class="field-heading">
                    Lock date
                    <tooltip tip="Students will not be able to fill in the entry anymore after this date"/>
                </h2>
                <flat-pickr
                    v-model="currentPreset.lock_date"
                    class="multi-form theme-input full-width"
                    :config="lockDateConfig"
                />
            </b-col>
        </b-row>
        <div v-else>
            <h2 class="field-heading required">
                Due date
                <tooltip
                    tip="Students are expected to have reached the amount of points below by this date,
                    but new entries can still be added until the assignment lock date"
                />
            </h2>
            <flat-pickr
                v-model="currentPreset.due_date"
                class="multi-form theme-input full-width"
                :config="progressDateConfig"
                @on-change="$emit('change-due-date')"
            />
        </div>

        <h2 class="field-heading">
            Description
        </h2>
        <b-textarea
            v-model="currentPreset.description"
            class="multi-form theme-input"
            placeholder="Description"
        />

        <div v-if="currentPreset.type === 'd'">
            <h2 class="field-heading required">
                Preset Template
                <tooltip tip="The template students can use for this entry"/>
            </h2>
            <div class="d-flex">
                <b-form-select
                    v-model="currentPreset.template"
                    class="multi-form mr-2"
                    :class="{ 'input-disabled' : templates.length === 0 }"
                >
                    <option
                        disabled
                        value=""
                    >
                        Please select a template
                    </option>
                    <option
                        v-for="template in templates"
                        :key="template.id"
                        :value="template"
                    >
                        {{ template.name }}
                    </option>
                </b-form-select>
                <b-button
                    v-if="showTemplatePreview"
                    class="multi-form delete-button flex-shrink-0"
                    @click="showTemplatePreview = false"
                >
                    <icon name="eye-slash"/>
                    Hide template
                </b-button>
                <b-button
                    v-if="!showTemplatePreview"
                    class="multi-form add-button flex-shrink-0"
                    @click="showTemplatePreview = true"
                >
                    <icon name="eye"/>
                    Preview template
                </b-button>
            </div>
            <div v-if="showTemplatePreview">
                <b-card class="no-hover">
                    <template-preview
                        v-if="currentPreset.template"
                        :template="currentPreset.template"
                    />
                    <span v-else>
                        Select a template to preview
                    </span>
                </b-card>
            </div>
        </div>
        <div v-else-if="currentPreset.type === 'p'">
            <h2 class="field-heading required">
                Amount of points
                <tooltip
                    tip="The amount of points students should have achieved by the deadline of this node to be on
                    schedule, new entries can still be added until the assignment's lock date"
                />
            </h2>
            <b-input
                v-model="currentPreset.target"
                type="number"
                class="theme-input"
                placeholder="Amount of points"
                min="1"
                :max="assignmentDetails.points_possible"
            />
        </div>
        <b-button
            v-if="!newPreset"
            class="delete-button full-width mt-2"
            @click.prevent="emitDeletePreset"
        >
            <icon name="trash"/>
            Remove preset
        </b-button>
    </b-card>
</template>

<script>
import templatePreview from '@/components/template/TemplatePreview.vue'
import tooltip from '@/components/assets/Tooltip.vue'

export default {
    components: {
        templatePreview,
        tooltip,
    },
    props: ['newPreset', 'currentPreset', 'templates', 'assignmentDetails'],
    data () {
        return {
            showTemplatePreview: false,
        }
    },
    computed: {
        unlockDateConfig () {
            let maxDate

            if (this.currentPreset.due_date) {
                maxDate = this.currentPreset.due_date
            } else if (this.currentPreset.lock_date) {
                maxDate = this.currentPreset.lock_date
            } else if (this.assignmentDetails.due_date) {
                maxDate = this.assignmentDetails.due_date
            } else {
                maxDate = this.assignmentDetails.lock_date
            }

            return Object.assign({}, {
                minDate: this.assignmentDetails.unlock_date,
                maxDate,
            }, this.$root.flatPickrTimeConfig)
        },
        dueDateConfig () {
            let minDate
            let maxDate

            if (this.currentPreset.unlock_date) {
                minDate = this.currentPreset.unlock_date
            } else {
                minDate = this.assignmentDetails.unlock_date
            }

            if ((this.currentPreset.lock_date && new Date(this.currentPreset.lock_date) < new Date(maxDate))
                || !maxDate) {
                maxDate = this.currentPreset.lock_date
            }

            if ((this.assignmentDetails.due_date && new Date(this.assignmentDetails.due_date) < new Date(maxDate))
                || !maxDate) {
                maxDate = this.assignmentDetails.due_date
            }

            if (!maxDate) {
                maxDate = this.assignmentDetails.lock_date
            }

            return Object.assign({}, {
                minDate,
                maxDate,
            }, this.$root.flatPickrTimeConfig)
        },
        lockDateConfig () {
            let minDate

            if (this.currentPreset.due_date) {
                minDate = this.currentPreset.due_date
            } else if (this.currentPreset.unlock_date) {
                minDate = this.currentPreset.unlock_date
            } else {
                minDate = this.assignmentDetails.unlock_date
            }

            return Object.assign({}, {
                minDate,
                maxDate: this.assignmentDetails.lock_date,
            }, this.$root.flatPickrTimeConfig)
        },
        progressDateConfig () {
            const minDate = this.assignmentDetails.unlock_date
            let maxDate

            if (this.assignmentDetails.due_date) {
                maxDate = this.assignmentDetails.due_date
            } else {
                maxDate = this.assignmentDetails.lock_date
            }

            return Object.assign({}, {
                minDate,
                maxDate,
            }, this.$root.flatPickrTimeConfig)
        },
    },
    methods: {
        emitDeletePreset () {
            if (window.confirm('Are you sure you want to remove this preset from this format?')) {
                this.$emit('delete-preset')
            }
        },
    },
}
</script>