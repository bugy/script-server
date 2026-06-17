import {forEachKeyValue, isNull} from "@/common/utils/common";

export function parametersToFormData(parameterValues) {
    const formData = new FormData();

    forEachKeyValue(parameterValues, function (parameter, value) {
        if (Array.isArray(value)) {
            for (let i = 0; i < value.length; i++) {
                const valueElement = value[i];
                formData.append(parameter, valueElement);
            }
        } else if (!isNull(value)) {
            formData.append(parameter, value);
        }
    });

    return formData;
}