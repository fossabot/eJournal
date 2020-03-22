<template>
    <b-card class="no-hover">
        <b-form
            @submit.prevent="onSubmit"
            @reset.prevent="onReset"
        >
            <h2 class="theme-h2 field-heading">
                Institute name
            </h2>
            <b-input
                v-model="instituteName"
                class="mb-2 mr-sm-2 mb-sm-0 multi-form theme-input"
                type="text"
                placeholder="Institute name"
            />
            <!-- TODO less placeholdery -->
            <b-button
                class="float-right delete-button"
                type="reset"
            >
                <icon name="undo"/>
                Reset
            </b-button>
            <b-button
                class="float-right add-button"
                type="submit"
            >
                <icon name="save"/>
                Save
            </b-button>
        </b-form>
    </b-card>
</template>

<script>
export default {
    name: 'EditHome',
    data () {
        return {
            instituteName: '',
        }
    },
    methods: {
        onSubmit () {
            /* TODO: Insert submission API. */
        },
        onReset (evt) {
            evt.preventDefault()
            /* Reset form values */
            this.instituteName = ''

            /* Trick to reset/clear native browser form validation state */
            this.show = false
            this.$nextTick(() => { this.show = true })
        },
    },
}
</script>
