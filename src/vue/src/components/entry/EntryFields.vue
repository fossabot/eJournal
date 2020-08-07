<template>
    <div v-if="edit">
        <div
            v-for="field in orderedFields"
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
                v-model="content[field.id].data"
                class="theme-input"
                rows="1"
            />
            <reset-wrapper
                v-if="field.type == 'd'"
                v-model="content[field.id].data"
            >
                <flat-pickr
                    v-model="content[field.id].data"
                    class="full-width"
                    :config="$root.flatPickrConfig"
                />
            </reset-wrapper>
            <reset-wrapper
                v-if="field.type == 'dt'"
                v-model="content[field.id].data"
            >
                <flat-pickr
                    v-model="content[field.id].data"
                    class="full-width"
                    :config="$root.flatPickrTimeConfig"
                />
            </reset-wrapper>
            <file-upload-input
                v-else-if="field.type == 'f'"
                :placeholder="content[field.id].data ? content[field.id].data.file_name : null"
                :acceptedFiletype="field.options ? '.' + field.options.split(', ').join(', .') : '*/*'"
                :maxSizeBytes="$root.maxFileSizeBytes"
                :autoUpload="true"
                :aID="$route.params.aID"
                :contentID="content[field.id].contentID"
                @uploadingFile="$emit('uploadingFile')"
                @fileUploadFailed="$emit('finishedUploadingFile')"
                @fileUploadSuccess="content[field.id].data = $event; $emit('finishedUploadingFile')"
            />
            <b-input
                v-else-if="field.type == 'v'"
                v-model="content[field.id].data"
                placeholder="Enter a YouTube URL"
                class="theme-input"
            />
            <text-editor
                v-else-if="field.type == 'rt'"
                :id="'rich-text-editor-field-' + field.id"
                :key="'rich-text-editor-field-' + field.id"
                v-model="content[field.id].data"
                @startedUploading="$emit('uploadingFile')"
                @finishedUploading="$emit('finishedUploadingFile')"
            />
            <url-input
                v-else-if="field.type == 'u'"
                placeholder="Enter a URL"
                @correctUrlInput="content[field.id].data = $event"
            />
            <b-form-select
                v-else-if="field.type == 's'"
                v-model="content[field.id].data"
                :options="parseSelectionOptions(field.options)"
                class="theme-select"
            />
        </div>
    </div>
    <!-- Display section -->
    <div v-else>
        <div
            v-for="field in displayFields"
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
            >{{ content[field.id].data }}</span>
            <span
                v-else-if="field.type == 'd'"
                class="show-enters"
            >{{ $root.beautifyDate(content[field.id].data, true, false) }}</span>
            <span
                v-else-if="field.type == 'dt'"
                class="show-enters"
            >{{ $root.beautifyDate(content[field.id].data) }}</span>
            <file-display
                v-else-if="field.type == 'f'"
                :file="content[field.id].data"
            />
            <b-embed
                v-else-if="field.type == 'v'"
                :src="youtubeEmbedFromURL(content[field.id].data)"
                type="iframe"
                aspect="16by9"
                allowfullscreen
            />
            <sandboxed-iframe
                v-else-if="field.type == 'rt'"
                :content="content[field.id].data"
            />
            <a
                v-else-if="field.type == 'u'"
                :href="content[field.id].data"
            >
                {{ content[field.id].data }}
            </a>
            <span v-else-if="field.type == 's'">{{ content[field.id].data }}</span>
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
        content: {
            default: false,
        },
        edit: {
            type: Boolean,
            required: true,
        },
        nodeID: {
            required: true,
        },
        entryID: {
            default: '-1',
        },
    },
    computed: {
        orderedFields () {
            return this.template.field_set.slice().sort((a, b) => a.location - b.location)
        },
        displayFields () {
            return this.orderedFields.filter(field => this.content[field.id].data)
        },
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
            // for (let i = 0; i < this.content.length; i++) {
            //     if (this.content[field.id].data !== null && this.content[field.id].data !== '') {
            //         return true
            //     }
            // }
            return false
        },
    },
}
</script>
