export default function (value: string) {
    const date = new Date(value + 'Z'); // append Z to force parsing as UTC

    if (isNaN(date.valueOf())) {
        return date.toString();
    }

    return date.toLocaleString();
}
