<template>
    <span class="number-badge">
        <b-badge
            v-if="rightNum === null || leftNum > 0"
            class="badge-part highlight"
            :class="{
                'info': leftNum > 0,
                'border-grey': leftNum <= 0,
                'left-number': rightNum !== null && rightNum > 0,
            }"
        >
            {{ leftNum ? Math.round(leftNum * 100) / 100 : 0 }}
        </b-badge>
        <b-badge
            v-if="rightNum > 0"
            class="badge-part"
            :class="{
                'right-number': leftNum > 0,
            }"
        >
            {{ rightNum ? Math.round(rightNum * 100) / 100 : 0 }}
        </b-badge>
    </span>
</template>

<script>
export default {
    props: {
        leftNum: {
            required: true,
            Number,
        },
        rightNum: {
            required: false,
            default: null,
            Number,
        },
    },
}
</script>

<style lang="sass">
@import '~sass/modules/colors.sass'
.number-badge
    .badge-part
        background-color: white
        color: $theme-dark-blue
        font-family: 'Roboto Condensed', sans-serif
        font-size: 1em
        border-radius: 5px !important
        border: 1px solid #CCCCCC
        &.right-number
            border-top-left-radius: 0 !important
            border-bottom-left-radius: 0 !important
            border-left: 0px !important
        &.left-number
            border-top-right-radius: 0 !important
            border-bottom-right-radius: 0 !important
            border-right: 0px !important
    .highlight
        background-color: $theme-dark-blue
        color: white!important
</style>
