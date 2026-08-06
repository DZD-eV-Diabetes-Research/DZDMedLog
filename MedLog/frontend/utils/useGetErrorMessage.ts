import {isFastAPIError, isFastAPIValidationError, isFetchError} from "~/type-helper";

export default function (errorObject: unknown): string {
    const error = isRef(errorObject) ? errorObject.value : errorObject;

    if (isFetchError(error) || isNuxtError(error)) {
        if (isFastAPIValidationError(error.data) && error.data.detail) {
            return error.data.detail.map(item => {
                return `[${item.loc.join('/')}] ${item.msg}`;
            }).join(', ');
        } else if (isFastAPIError(error.data)) {
            if (typeof error.data.detail == 'object' && 'message' in error.data.detail) {
                return String(error.data.detail.message);
            }

            return String(error.data.detail);
        }

        return error.message ?? error.statusMessage ?? "";
    }

    return String(error);
}
