export default defineAppConfig({
    ui: {
        notification: {
            default: {
                color: "red",
                icon: "i-heroicons-exclamation-circle",
                timeout: 10000,
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
