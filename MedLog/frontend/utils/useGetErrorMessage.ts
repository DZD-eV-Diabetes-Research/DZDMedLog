import {isFastAPIError, isFastAPIValidationError, isFetchError} from "~/type-helper";

export default function (error: unknown): string {
    if (isNuxtError(error)) {
        return error.message ?? error.statusMessage ?? "";
    } else if (isFetchError(error)) {
        if (isFastAPIValidationError(error.data) && error.data.detail) {
            return error.data.detail.map(item => {
                return `[${item.loc.join('/')}] ${item.msg}`;
            }).join(', ');
        } else if (isFastAPIError(error.data)) {
            return String(error.data.detail);
        }
    }

    return String(error);
}
