<!-- Loads a preview of a template. nID are required but unused as autoupload is disabled. -->
<template>
    <div>
        <h2 class="theme-h2">
            {{ template.name }}
        </h2>
        <div
            v-for="(field, i) in sortedFields"
            :key="field.eID"
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
                class="theme-input input-disabled"
            />
            <file-upload-input
                v-else-if="field.type == 'i'"
                :acceptedFiletype="'image/*'"
                :maxSizeBytes="$root.maxFileSizeBytes"
                :autoUpload="false"
                :aID="$route.params.aID"
                :nID="'1'"
                class="input-disabled"
            />
            <file-upload-input
                v-else-if="field.type == 'f'"
                :acceptedFiletype="'*/*'"
                :maxSizeBytes="$root.maxFileSizeBytes"
                :autoUpload="false"
                :aID="$route.params.aID"
                :nID="'1'"
                class="input-disabled"
            />
            <b-input
                v-else-if="field.type == 'v'"
                class="theme-input input-disabled"
                placeholder="Enter YouTube URL..."
            />
            <file-upload-input
                v-else-if="field.type == 'p'"
                :acceptedFiletype="'application/pdf'"
                :maxSizeBytes="$root.maxFileSizeBytes"
                :autoUpload="false"
                :aID="$route.params.aID"
                :nID="'1'"
                class="input-disabled"
            />
            <text-editor
                v-else-if="field.type == 'rt'"
                :id="'rich-text-editor-preview-field-' + i"
                :key="'rich-text-editor-preview-field-' + i"
                class="input-disabled"
            />
            <url-input
                v-else-if="field.type == 'u'"
                class="input-disabled"
            />
            <flat-pickr
                v-else-if="field.type == 'd'"
                :config="$root.flatpickrConfig"
                class="input-disabled full-width"
            />
            <flat-pickr
                v-else-if="field.type == 'dt'"
                :config="$root.flatpickrTimeConfig"
                class="input-disabled full-width"
            />
            <b-form-select
                v-else-if="field.type == 's'"
                :value="null"
                :options="parseSelectionOptions(field.options)"
                class="theme-select input-disabled"
            />
        </div>
    </div>
</template>

<script>
import fileUploadInput from '@/components/assets/file_handling/FileUploadInput.vue'
import textEditor from '@/components/assets/TextEditor.vue'
import urlInput from '@/components/assets/UrlInput.vue'
import sandboxedIframe from '@/components/assets/SandboxedIframe.vue'

export default {
    components: {
        fileUploadInput,
        textEditor,
        urlInput,
        sandboxedIframe,
    },
    props: ['template'],
    computed: {
        sortedFields () {
            return this.template.field_set.slice(0).sort((a, b) => a.location - b.location)
        },
    },
    methods: {
        parseSelectionOptions (fieldOptions) {
            if (!fieldOptions) {
                return [{ value: null, text: 'Please select an option...' }]
            }
            const options = JSON.parse(fieldOptions).filter(e => e).map(x => Object({ value: x, text: x }))
            options.unshift({ value: null, text: 'Please select an option...' })
            return options
        },
    },
}
</script>
