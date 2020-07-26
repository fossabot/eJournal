<template>
    <b-card
        :class="$root.getBorderClass($route.params.cID)"
        class="no-hover"
    >
        <template
            v-if="addNode.templates.length > 1"
        >
            <h2 class="theme-h2 mb-2">
                New entry
            </h2>
            <b-form-select
                v-model="selectedTemplate"
                class="theme-select mb-2"
            >
                <option
                    :value="null"
                    disabled
                >
                    Please select a template
                </option>
                <option
                    v-for="template in addNode.templates"
                    :key="template.id"
                    :value="template"
                >
                    {{ template.name }}
                </option>
            </b-form-select>
        </template>
        <template v-if="selectedTemplate !== null">
            <hr
                v-if="addNode.templates.length > 1"
                class="mt-2 mb-2"
            />
            <entry-preview
                ref="entry-prev"
                :template="selectedTemplate"
                :nID="addNode.nID"
                :jID="jID"
                @posted="entryPosted"
            />
        </template>
    </b-card>
</template>

<script>
import entryPreview from '@/components/entry/EntryPreview.vue'

export default {
    components: {
        entryPreview,
    },
    props: {
        addNode: {
            required: true,
        },
        jID: {
            required: true,
        },
    },
    data () {
        return {
            selectedTemplate: null,
            infoEntry: null,
        }
    },
    created () {
        if (this.addNode.templates.length === 1) {
            this.selectedTemplate = this.addNode.templates[0]
        }
    },
    methods: {
        entryPosted (data) {
            this.$emit('posted', data)
        },
        checkChanges () {
            /* No template is selected, so no changes. */
            if (!this.addNode.templates.length || !this.selectedTemplate) {
                return false
            }

            return this.$refs['entry-prev'].checkChanges()
        },
    },
}
</script>
