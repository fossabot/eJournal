<template>
    <b-card class="no-hover">
        <div class="d-flex">
            <b-button
                :class="{'active': mode === 'edit'}"
                class="multi-form change-button flex-basis-100"
                @click="mode = 'edit'"
            >
                <icon name="edit"/>
                Edit
            </b-button>
            <b-button
                :class="{'active': mode === 'preview'}"
                class="multi-form add-button flex-basis-100"
                @click="mode='preview'"
            >
                <icon name="eye"/>
                Preview
            </b-button>
        </div>
        <hr/>
        <div v-show="mode === 'edit'">
            <b-input
                id="template-name"
                v-model="template.name"
                class="mr-sm-2 multi-form theme-input"
                placeholder="Template name"
                required
            />
            <div
                v-if="template.preset_only"
                class="template-availability"
            >
                <b-button
                    class="delete-button"
                    @click.stop
                    @click="togglePresetOnly"
                >
                    <icon name="lock"/>
                    Preset-only
                </b-button>
                <icon
                    name="info-circle"
                    class="shift-up-3"
                />
                This template can only be used for preset entries you add to the timeline
            </div>
            <div
                v-if="!template.preset_only"
                class="template-availability"
            >
                <b-button
                    class="add-button"
                    @click.stop
                    @click="togglePresetOnly"
                >
                    <icon name="unlock"/>
                    Unlimited
                </b-button>
                <icon
                    name="info-circle"
                    class="shift-up-3"
                />
                This template can be freely used by students as often as they want<br/>
            </div>
            <draggable
                v-model="template.field_set"
                handle=".handle"
                @start="startDrag"
                @end="endDrag"
                @update="onUpdate"
            >
                <b-card
                    v-for="field in template.field_set"
                    :key="field.location"
                    class="field-card"
                >
                    <b-row
                        alignH="between"
                        noGutters
                    >
                        <b-col
                            cols="12"
                            sm="10"
                            lg="11"
                        >
                            <b-input
                                v-model="field.title"
                                class="multi-form theme-input"
                                placeholder="Field title"
                                required
                            />
                            <text-editor
                                v-if="showEditors"
                                :id="`rich-text-editor-field-${template.id}-${field.location}`"
                                :key="`rich-text-editor-field-${template.id}-${field.location}`"
                                v-model="field.description"
                                :basic="true"
                                :displayInline="true"
                                :minifiedTextArea="true"
                                class="multi-form"
                                placeholder="Optional description"
                                required
                            />
                            <div class="d-flex">
                                <b-select
                                    v-model="field.type"
                                    :options="fieldTypes"
                                    class="theme-select multi-form mr-2"
                                    @change="field.options = ''"
                                />
                                <b-button
                                    v-if="!field.required"
                                    class="optional-field-template float-right multi-form"
                                    @click.stop
                                    @click="field.required = !field.required"
                                >
                                    <icon name="asterisk"/>
                                    Optional
                                </b-button>
                                <b-button
                                    v-if="field.required"
                                    class="required-field-template float-right multi-form"
                                    @click.stop
                                    @click="field.required = !field.required"
                                >
                                    <icon name="asterisk"/>
                                    Required
                                </b-button>
                            </div>

                            <!-- Field Options -->
                            <div v-if="field.type == 's'">
                                <!-- Event targeting allows us to access the input value -->
                                <div class="d-flex">
                                    <b-input
                                        class="multi-form mr-2 theme-input"
                                        placeholder="Enter an option"
                                        @keyup.enter.native="addSelectionOption($event.target, field)"
                                    />
                                    <b-button
                                        class="float-right multi-form add-button"
                                        @click.stop="addSelectionOption($event.target.previousElementSibling, field)"
                                    >
                                        <icon name="plus"/>
                                        Add
                                    </b-button>
                                </div>
                                <div v-if="field.options">
                                    <b-button
                                        v-for="(option, index) in JSON.parse(field.options)"
                                        :key="index"
                                        class="delete-button mr-2 mb-2"
                                        @click.stop="removeSelectionOption(option, field)"
                                    >
                                        <icon name="trash"/>
                                        {{ option }}
                                    </b-button>
                                </div>
                            </div>
                        </b-col>
                        <b-col
                            cols="12"
                            sm="2"
                            lg="1"
                            class="icon-box"
                        >
                            <div class="handle d-inline d-sm-block">
                                <icon
                                    class="move-icon"
                                    name="arrows-alt"
                                    scale="1.75"
                                />
                            </div>
                            <icon
                                class="trash-icon"
                                name="trash"
                                scale="1.75"
                                @click.native="removeField(field.location)"
                            />
                        </b-col>
                    </b-row>
                </b-card>
                <div class="invisible"/>
            </draggable>
            <b-button
                class="add-button full-width"
                @click="addField"
            >
                <icon name="plus"/>
                Add field
            </b-button>
        </div>
        <template-preview
            v-if="mode !== 'edit'"
            :template="template"
        />
    </b-card>
</template>

<script>
import templatePreview from '@/components/template/TemplatePreview.vue'
import textEditor from '@/components/assets/TextEditor.vue'
import draggable from 'vuedraggable'

export default {
    components: {
        draggable,
        textEditor,
        templatePreview,
    },
    props: {
        template: {
            required: true,
        },
    },
    data () {
        return {
            fieldTypes: {
                t: 'Text',
                rt: 'Rich Text',
                i: 'Image',
                p: 'PDF',
                f: 'File',
                v: 'YouTube Video',
                u: 'URL',
                d: 'Date',
                dt: 'Date Time',
                s: 'Selection',
            },
            mode: 'edit',
            selectedLocation: null,
            showEditors: true,
        }
    },
    created () {
        this.template.field_set.sort((a, b) => a.location - b.location)
    },
    methods: {
        updateLocations () {
            for (let i = 0; i < this.template.field_set.length; i++) {
                this.template.field_set[i].location = i
            }
        },
        addField () {
            const newField = {
                type: 'rt',
                title: '',
                description: '',
                options: null,
                location: this.template.field_set.length,
                required: true,
            }

            this.template.field_set.push(newField)
        },
        removeField (location) {
            if (this.template.field_set[location].title
                ? window.confirm(
                    `Are you sure you want to remove "${this.template.field_set[location].title}" from this template?`)
                : window.confirm('Are you sure you want to remove this field from this template?')) {
                this.template.field_set.splice(location, 1)
            }

            this.updateLocations()
        },
        startDrag () {
            this.showEditors = false
        },
        endDrag () {
            this.showEditors = true
        },
        onUpdate () {
            this.updateLocations()
        },
        addSelectionOption (target, field) {
            if (target.value.trim()) {
                if (!field.options) {
                    field.options = JSON.stringify([])
                }
                const options = JSON.parse(field.options)
                options.push(target.value.trim())
                field.options = JSON.stringify(options)
                target.value = ''
                target.focus()
            }
        },
        removeSelectionOption (option, field) {
            const options = JSON.parse(field.options)
            options.splice(options.indexOf(option.trim()), 1)
            field.options = JSON.stringify(options)
        },
        togglePresetOnly () {
            this.template.preset_only = !this.template.preset_only
        },
    },
}
</script>

<style lang="sass">
@import '~sass/modules/colors.sass'
@import '~sass/modules/breakpoints.sass'

.optional-field-template
    background-color: white
    color: $theme-dark-blue !important
    svg
        fill: $theme-medium-grey

.required-field-template
    background-color: $theme-dark-blue !important
    color: white !important
    svg, &:hover:not(.no-hover) svg
        fill: $theme-red !important

#template-name
    font-weight: bold
    font-size: 1.8em
    font-family: 'Roboto', sans-serif
    color: $theme-dark-blue

.sortable-chosen .card
    background-color: $theme-dark-grey

.sortable-ghost
    visibility: hidden

.sortable-drag .card
    visibility: visible

.icon-box
    text-align: center

.handle
    text-align: center
    padding-bottom: 7px

.field-card:hover .move-icon, .field-card:hover .trash-icon
    fill: $theme-dark-blue !important

.handle:hover .move-icon
    cursor: grab
    fill: $theme-blue !important

.field-card:hover .trash-icon:hover
    fill: $theme-red !important

@include sm-max
    .icon-box
        margin-top: 10px

.template-availability
    font-weight: bold
    color: grey
    margin-bottom: 10px
    .btn
        margin-right: 20px
        @include md-max
            width: 100%
            margin-bottom: 10px
</style>
