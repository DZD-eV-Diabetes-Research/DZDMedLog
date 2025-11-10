export default function (value: string) {
    const date = new Date(value);

    if (isNaN(date.valueOf())) {
        return date.toString();
    }

    return date.toLocaleString();
}
