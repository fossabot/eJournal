<template>
    <div v-if="!displayMode">
        <div
            v-for="(field, i) in fieldsToEdit"
            :key="`node ${nodeID}-field-${field.id}`"
            class="multi-form"
        >
            <h2
                v-if="field.title"
                :class="{ 'required': field.required }"
                class="theme-h2 field-heading"
            >
                {{ field.title }}
            </h2>
            <sandboxed-iframe
                v-if="field.description"
                :content="field.description"
            />

            <b-input
                v-if="field.type == 't'"
                v-model="completeContent[i].data"
                class="theme-input"
                rows="1"
            />
            <reset-wrapper
                v-if="field.type == 'd'"
                v-model="completeContent[i].data"
            >
                <flat-pickr
                    v-model="completeContent[i].data"
                    class="full-width"
                    :config="$root.flatPickrConfig"
                />
            </reset-wrapper>
            <reset-wrapper
                v-if="field.type == 'dt'"
                v-model="completeContent[i].data"
            >
                <flat-pickr
                    v-model="completeContent[i].data"
                    class="full-width"
                    :config="$root.flatPickrTimeConfig"
                />
            </reset-wrapper>
            <file-upload-input
                v-else-if="field.type == 'f'"
                :placeholder="completeContent[i].data ? completeContent[i].data.file_name : null"
                :acceptedFiletype="field.options ? '.' + field.options.split(', ').join(', .') : '*/*'"
                :maxSizeBytes="$root.maxFileSizeBytes"
                :autoUpload="true"
                :aID="$route.params.aID"
                :contentID="completeContent[i].contentID"
                @uploadingFile="$emit('uploadingFile')"
                @fileUploadFailed="$emit('finishedUploadingFile')"
                @fileUploadSuccess="completeContent[i].data = $event; $emit('finishedUploadingFile')"
            />
            <b-input
                v-else-if="field.type == 'v'"
                v-model="completeContent[i].data"
                placeholder="Enter a YouTube URL"
                class="theme-input"
            />
            <text-editor
                v-else-if="field.type == 'rt'"
                :id="'rich-text-editor-field-' + i"
                :key="'rich-text-editor-field-' + i"
                v-model="completeContent[i].data"
                @startedUploading="$emit('uploadingFile')"
                @finishedUploading="$emit('finishedUploadingFile')"
            />
            <url-input
                v-else-if="field.type == 'u'"
                placeholder="Enter a URL"
                @correctUrlInput="completeContent[i].data = $event"
            />
            <b-form-select
                v-else-if="field.type == 's'"
                v-model="completeContent[i].data"
                :options="parseSelectionOptions(field.options)"
                class="theme-select"
            />
        </div>
    </div>
    <!-- Display section -->
    <div v-else>
        <div
            v-for="field in fieldsToDisplay"
            :key="`node-${nodeID}-field-${field.id}`"
            class="multi-form"
        >
            <h2
                v-if="field.title"
                :class="{ 'required': field.required }"
                class="theme-h2 field-heading"
            >
                {{ field.title }}
            </h2>
            <span
                v-if="field.type == 't'"
                class="show-enters"
            >{{ completeContent[field.location].data }}</span>
            <span
                v-else-if="field.type == 'd'"
                class="show-enters"
            >{{ $root.beautifyDate(completeContent[field.location].data, true, false) }}</span>
            <span
                v-else-if="field.type == 'dt'"
                class="show-enters"
            >{{ $root.beautifyDate(completeContent[field.location].data) }}</span>
            <file-display
                v-else-if="field.type == 'f'"
                :file="completeContent[field.location].data"
            />
            <b-embed
                v-else-if="field.type == 'v'"
                :src="youtubeEmbedFromURL(completeContent[field.location].data)"
                type="iframe"
                aspect="16by9"
                allowfullscreen
            />
            <sandboxed-iframe
                v-else-if="field.type == 'rt'"
                :content="completeContent[field.location].data"
            />
            <a
                v-else-if="field.type == 'u'"
                :href="completeContent[field.location].data"
            >
                {{ completeContent[field.location].data }}
            </a>
            <span v-else-if="field.type == 's'">{{ completeContent[field.location].data }}</span>
        </div>
    </div>
</template>

<script>
import fileUploadInput from '@/components/assets/file_handling/FileUploadInput.vue'
import textEditor from '@/components/assets/TextEditor.vue'
import urlInput from '@/components/assets/UrlInput.vue'
import fileDisplay from '@/components/assets/file_handling/FileDisplay.vue'
import sandboxedIframe from '@/components/assets/SandboxedIframe.vue'

export default {
    components: {
        fileUploadInput,
        textEditor,
        urlInput,
        fileDisplay,
        sandboxedIframe,
    },
    props: {
        template: {
            required: true,
        },
        completeContent: {
            default: false,
        },
        displayMode: {
            type: Boolean,
            required: true,
        },
        nodeID: {
            required: true,
        },
        journalID: {
            default: null,
            required: false,
        },
        entryID: {
            default: '-1',
        },
    },
    computed: {
        fieldsToDisplay () {
            return this.template.field_set.filter((field, i) => (field.required || this.completeContent[i].data))
        },
        fieldsToEdit () {
            return this.template.field_set
        },
    },
    created () {
        this.template.field_set.sort((a, b) => a.location - b.location)
    },
    methods: {
        // from https://stackoverflow.com/a/9102270
        youtubeEmbedFromURL (url) {
            const regExp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
            const match = url.match(regExp)
            if (match && match[2].length === 11) {
                return `https://www.youtube.com/embed/${match[2]}?rel=0&amp;showinfo=0`
            } else {
                this.$toasted.error('A YouTube video field contained an invalid URL.')
                return null
            }
        },
        parseSelectionOptions (fieldOptions) {
            if (!fieldOptions) {
                return [{ value: null, text: 'Please select an option...' }]
            }
            const options = JSON.parse(fieldOptions).filter(e => e).map(x => Object({ value: x, text: x }))
            options.unshift({ value: null, text: 'Please select an option...' })
            return options
        },
        checkChanges () {
            for (let i = 0; i < this.completeContent.length; i++) {
                if (this.completeContent[i].data !== null && this.completeContent[i].data !== '') {
                    return true
                }
            }
            return false
        },
    },
}
</script>
