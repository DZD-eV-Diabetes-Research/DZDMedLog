export default function (value: string, dateOnly: boolean = false) {
    const date = new Date(value + 'Z'); // append Z to force parsing as UTC

    if (isNaN(date.valueOf())) {
        return date.toString();
    }

    return dateOnly ? date.toLocaleDateString() : date.toLocaleString();
}
