<template>
    <div>
        <b-card class="no-hover">
            <b-input class="mb-2 mr-sm-2 mb-sm-0 multi-form theme-input" id="templateName" v-model="template.name" placeholder="Template name" required/>
            <draggable v-model="template.fields" @start="drag=true" @end="drag=false" @update="onUpdate" :options="{ handle:'.handle' }">
                <div v-for="field in template.fields" :key="field.location">
                    <b-card class="field-card">
                        <b-row align-h="between" no-gutters>
                            <b-col cols="12" sm="10" lg="11">
                                <b-input class="mb-2 mr-sm-2 mb-sm-0 multi-form theme-input" v-model="field.title" placeholder="Field title" required/>
                                <b-select :options="fieldTypes" v-model="field.type"></b-select>
                            </b-col>
                            <b-col cols="12" sm="2" lg="1" class="icon-box">
                                <div class="handle d-inline d-sm-block">
                                    <icon class="move-icon" name="arrows" scale="1.75"/>
                                </div>
                                <icon class="trash-icon" @click.native="removeField(field.location)" name="trash" scale="1.75"/>
                            </b-col>
                        </b-row>
                    </b-card>
                </div>
                <div class="invisible"></div>
            </draggable>
            <b-button class="add-button full-width" @click="addField">
                <icon name="plus"/>
                Add field
            </b-button>
        </b-card>
    </div>
</template>

<script>
import ContentSingleColumn from '@/components/columns/ContentSingleColumn.vue'
import icon from 'vue-awesome/components/Icon'
import draggable from 'vuedraggable'

export default {
    props: {
        template: {
            required: true
        }
    },
    data () {
        return {
            fieldTypes: {
                't': 'Text',
                'rt': 'Rich Text',
                'i': 'Image',
                'p': 'PDF',
                'f': 'File',
                'v': 'YouTube Video'
            }
        }
    },
    components: {
        'content-single-column': ContentSingleColumn,
        icon,
        'draggable': draggable
    },
    methods: {
        updateLocations () {
            for (var i = 0; i < this.template.fields.length; i++) {
                this.template.fields[i].location = i
            }
        },
        addField () {
            var newField = {
                'type': 't',
                'title': '',
                'location': this.template.fields.length
            }

            this.template.fields.push(newField)
        },
        removeField (location) {
            if (confirm('Are you sure you want to remove "' + this.template.fields[location].title + '" from this template?')) {
                this.template.fields.splice(location, 1)
            }

            this.updateLocations()
        },
        onUpdate () {
            this.updateLocations()
        }
    }
}
</script>

<style lang="sass">
@import '~sass/modules/colors.sass'
@import '~sass/modules/breakpoints.sass'

#templateName
    font-weight: bold
    font-size: 35px
    font-family: 'Roboto', sans-serif
    color: $theme-dark-blue

.field-card
    background-color: $theme-medium-grey

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

.move-icon
    fill: $theme-dark-grey

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
</style>