<template>
    <b-row
        class="content-single-column"
        noGutters
    >
        <b-col
            :class="'content ' + extraClasses"
            lg="8"
            xl="6"
            offsetLg="2"
            offsetXl="3"
        >
            <slot/>
        </b-col>
    </b-row>
</template>

<script>
export default {
    name: 'ContentSingleColumn',
    props: {
        extraClasses: {
            default: '',
        },
    },
}
</script>
