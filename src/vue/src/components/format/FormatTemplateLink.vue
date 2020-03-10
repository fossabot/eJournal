<!--
    Used in a card in the format editor to open template editor, toggle availability, delete templates from pool.
-->

<template>
    <b-card
        :class="$root.getBorderClass(template.id)"
        class="template-card"
        @click="$emit('edit-template')"
    >
        <icon
            name="trash"
            class="trash-icon ml-2 float-right"
            @click.native.stop="emitDeleteTemplate"
        />
        <icon
            name="edit"
            class="edit-icon float-right"
        />
        <b
            v-if="template.name"
            class="d-block field-heading"
        >
            {{ template.name }}
        </b>
        <b
            v-else
            class="d-block text-red field-heading"
        >
            Untitled template
        </b>
    </b-card>
</template>

<script>
export default {
    props: ['template'],
    methods: {
        emitDeleteTemplate () {
            if (window.confirm(
                `Are you sure you want to delete template "${this.template.name}" from this assignment?`)) {
                this.$emit('delete-template')
            }
        },
        togglePresetOnly () {
            this.template.preset_only = !this.template.preset_only
        },
    },
}
</script>

<style lang="sass">
@import '~sass/modules/colors.sass'

.template-card
    .edit-icon
        margin-top: 1px
    .edit-icon, .trash-icon
        width: 0px
        visibility: hidden
    &:hover
        .edit-icon, .trash-icon
            visibility: visible
            width: auto
</style>
