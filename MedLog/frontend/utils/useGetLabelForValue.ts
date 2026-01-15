export default function (options: { value: string; label: string }[], givenValue?: string | null): string {
    if (!givenValue) {
        return ''
    }

    return options.find(option => option.value == givenValue)?.label ?? givenValue
}
