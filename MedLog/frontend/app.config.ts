export default defineAppConfig({
    ui: {
        notification: {
            default: {
                color: "red",
                icon: "i-heroicons-exclamation-circle",
                timeout: 10000,
            },
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
