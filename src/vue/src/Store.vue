<script>
export default {
    debug: false,
    state: {
        cachedMap: {},
        filteredJournals: [],
    },
    setCachedMap (cachedMap) {
        this.state.cachedMap = cachedMap
    },
    setFilteredJournals (journals, order = true, groups = null, searchValue = null, sortBy = 'name') {
        function compare (a, b) {
            if (a < b) { return order ? 1 : -1 }
            if (a > b) { return order ? -1 : 1 }
            return 0
        }

        const sortOptions = {
            name: (a, b) => compare(a.name, b.name),
            username: (a, b) => {
                if (a.authors.length > 0 && b.authors.length > 0) {
                    return compare(a.authors[0].user.username, b.authors[0].user.username)
                } else if (a.authors.length > 0) {
                    return -1
                } else if (b.authors.length > 0) {
                    return 1
                }
                return 0
            },
            markingNeeded: (a, b) => compare(a.stats.submitted - a.stats.graded, b.stats.submitted - b.stats.graded),
            points: (a, b) => compare(a.stats.acquired_points, b.stats.acquired_points),
        }

        function groupFilter (journal) {
            if (groups === null) {
                return false
            }
            const groupsList = []
            journal.authors.forEach((student) => {
                if (student.user.groups) {
                    student.user.groups.forEach((group) => {
                        if (!groupsList.includes(group)) {
                            groupsList.push(group.id)
                        }
                    })
                }
            })

            return groups.some(group => groupsList.includes(group.id))
        }

        function searchFilter (journal) {
            return journal.name.toLowerCase().includes(searchValue.toLowerCase())
                || journal.authors.some(
                    author => author.user.username.toLowerCase().includes(searchValue.toLowerCase()))
                || journal.authors.some(
                    author => author.user.full_name.toLowerCase().includes(searchValue.toLowerCase()))
        }
        let filteredJournals = journals
        if (groups !== null && groups.length !== 0) {
            filteredJournals = filteredJournals.filter(groupFilter)
        }
        if (searchValue !== null && searchValue !== '') {
            filteredJournals = filteredJournals.filter(searchFilter)
        }
        filteredJournals.sort(sortOptions[sortBy])
        this.state.filteredJournals = filteredJournals
    },
    debugOn () {
        this.debug = true
    },
    debugOff () {
        this.debug = false
    },
    clearCache () {
        this.state.cachedMap = []
    },
}
</script>
