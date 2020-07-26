<!--
    Loads a preview of an Entry-Template and returns the filled in data to
    the parent once it's saved.
-->
<template>
    <div>
        <h2 class="theme-h2 mb-2">
            {{ template.name }}
        </h2>
        <sandboxed-iframe
            v-if="description"
            :content="description"
        />

        <entry-fields
            :template="template"
            :completeContent="completeContent"
            :displayMode="false"
            :nodeID="nID"
            @uploadingFile="uploadingFiles++"
            @finishedUploadingFile="uploadingFiles--"
        />

        <b-alert
            :show="dismissCountDown"
            dismissible
            variant="danger"
            @dismissed="dismissCountDown=0"
        >
            Some fields are empty or incorrectly formatted.
        </b-alert>
        <template v-if="Array.isArray(jID)">
            <div
                class="teacher-entry-grade"
            >
                <icon
                    v-b-tooltip:hover="'Grade to assign to all posted entries'"
                    name="info-circle"
                />
                Grade:
                <b-form-input
                    id="grade"
                    v-model="teacherEntryGrade"
                    type="number"
                    min="0"
                    class="theme-input mr-2"
                />
                <b-form-checkbox
                    v-model="teacherEntryPublishGrade"
                    class="d-inline-block"
                >
                    Published
                </b-form-checkbox>
            </div>
        </template>
        <b-button
            class="add-button float-right"
            :class="{ 'input-disabled': saveRequestInFlight || uploadingFiles > 0 }"
            @click="save"
        >
            <icon name="paper-plane"/>
            Post Entry
        </b-button>
    </div>
</template>

<script>
import entryFields from '@/components/entry/EntryFields.vue'

import entryAPI from '@/api/entry.js'

export default {
    components: {
        entryFields,
    },
    props: {
        template: {
            required: true,
        },
        nID: {
            required: true,
        },
        // Can be an array of journal IDs for teacher-initated entries.
        jID: {
            required: true,
        },
        description: {
            required: false,
            default: null,
        },
    },
    data () {
        return {
            completeContent: [],
            dismissSecs: 3,
            dismissCountDown: 0,
            showDismissibleAlert: false,
            saveRequestInFlight: false,
            uploadingFiles: 0,

            // For teacher-initated entries a grade can be added right away.
            teacherEntryGrade: null,
            teacherEntryPublishGrade: false,
        }
    },
    watch: {
        template () {
            this.completeContent = []
            this.setContent()
        },
    },
    created () {
        this.setContent()
    },
    methods: {
        setContent () {
            this.template.field_set.forEach((field) => {
                this.completeContent.push({
                    data: null,
                    id: field.id,
                })
            })
        },
        checkFilled () {
            for (let i = 0; i < this.completeContent.length; i++) {
                const content = this.completeContent[i]
                const field = this.template.field_set[i]
                if (field.required && !content.data) {
                    return false
                }
            }

            return true
        },
        checkChanges () {
            for (let i = 0; i < this.completeContent.length; i++) {
                if (this.completeContent[i].data !== null && this.completeContent[i].data !== '') {
                    return true
                }
            }
            return false
        },
        save () {
            if (this.checkFilled()) {
                if (Array.isArray(this.jID)) {
                    const params = {
                        journal_ids: this.jID,
                        template_id: this.template.id,
                        content: this.completeContent,
                    }
                    this.saveRequestInFlight = true
                    entryAPI.create(params)
                        .then((data) => {
                            this.saveRequestInFlight = false
                            this.$emit('posted', data)
                        })
                        .catch(() => { this.saveRequestInFlight = false })
                } else {
                    const params = {
                        journal_id: this.jID,
                        template_id: this.template.id,
                        content: this.completeContent,
                    }
                    if (this.nID > 0) {
                        params.node_id = this.nID
                    }
                    this.saveRequestInFlight = true
                    entryAPI.create(params)
                        .then((data) => {
                            this.saveRequestInFlight = false
                            this.$emit('posted', data)
                        })
                        .catch(() => { this.saveRequestInFlight = false })
                }
            } else {
                this.dismissCountDown = this.dismissSecs
            }
        },
    },
}
</script>

<style lang="sass">
.teacher-entry-grade
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
