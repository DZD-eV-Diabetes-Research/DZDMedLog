export default defineAppConfig({
    ui: {
        checkbox: {
            base: 'disabled:bg-gray-100',
        },
        input: {
            base: 'disabled:bg-gray-100',
        },
        notification: {
            default: {
                color: "red",
                icon: "i-heroicons-exclamation-circle",
                timeout: 10000,
            },
        },
        select: {
            base: 'disabled:bg-gray-100',
        },
        selectMenu: {
            default: {
                searchablePlaceholder: {
                    label: 'Suchen...'
                },
                empty: {
                    label: 'Keine Einträge.'
                },
                optionEmpty: {
                    label: 'Keine Ergebnisse für "{query}".'
                }
            },
        },
        table: {
            default: {
                emptyState: {
                    label: 'Keine Einträge',
                },
            },
        },
    },
})
