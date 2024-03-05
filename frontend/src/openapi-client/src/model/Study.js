/**
 * MedLog REST API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.0.1
 * 
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 *
 */

import ApiClient from '../ApiClient';
import DisplayName from './DisplayName';

/**
 * The Study model module.
 * @module model/Study
 * @version 0.0.1
 */
class Study {
    /**
     * Constructs a new <code>Study</code>.
     * @alias module:model/Study
     * @param name {String} The identifiying name of the study. This can not be changed later. Must be a '[Slug](https://en.wikipedia.org/wiki/Clean_URL#Slug)'; A human and machine reable string containing no spaces, only numbers, lowered latin-script-letters and dashes. If you need to change the name later, use the display name.
     */
    constructor(name) { 
        
        Study.initialize(this, name);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj, name) { 
        obj['name'] = name;
    }

    /**
     * Constructs a <code>Study</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/Study} obj Optional instance to populate.
     * @return {module:model/Study} The populated <code>Study</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new Study();

            if (data.hasOwnProperty('created_at')) {
                obj['created_at'] = ApiClient.convertToType(data['created_at'], 'Date');
            }
            if (data.hasOwnProperty('display_name')) {
                obj['display_name'] = DisplayName.constructFromObject(data['display_name']);
            }
            if (data.hasOwnProperty('deactivated')) {
                obj['deactivated'] = ApiClient.convertToType(data['deactivated'], 'Boolean');
            }
            if (data.hasOwnProperty('no_permissions')) {
                obj['no_permissions'] = ApiClient.convertToType(data['no_permissions'], 'Boolean');
            }
            if (data.hasOwnProperty('id')) {
                obj['id'] = ApiClient.convertToType(data['id'], 'String');
            }
            if (data.hasOwnProperty('name')) {
                obj['name'] = ApiClient.convertToType(data['name'], 'String');
            }
        }
        return obj;
    }

    /**
     * Validates the JSON data with respect to <code>Study</code>.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @return {boolean} to indicate whether the JSON data is valid with respect to <code>Study</code>.
     */
    static validateJSON(data) {
        // check to make sure all required properties are present in the JSON string
        for (const property of Study.RequiredProperties) {
            if (!data.hasOwnProperty(property)) {
                throw new Error("The required field `" + property + "` is not found in the JSON data: " + JSON.stringify(data));
            }
        }
        // validate the optional field `display_name`
        if (data['display_name']) { // data not null
          DisplayName.validateJSON(data['display_name']);
        }
        // ensure the json data is a string
        if (data['id'] && !(typeof data['id'] === 'string' || data['id'] instanceof String)) {
            throw new Error("Expected the field `id` to be a primitive type in the JSON string but got " + data['id']);
        }
        // ensure the json data is a string
        if (data['name'] && !(typeof data['name'] === 'string' || data['name'] instanceof String)) {
            throw new Error("Expected the field `name` to be a primitive type in the JSON string but got " + data['name']);
        }

        return true;
    }


}

Study.RequiredProperties = ["name"];

/**
 * @member {Date} created_at
 */
Study.prototype['created_at'] = undefined;

/**
 * @member {module:model/DisplayName} display_name
 */
Study.prototype['display_name'] = undefined;

/**
 * @member {Boolean} deactivated
 * @default false
 */
Study.prototype['deactivated'] = false;

/**
 * If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study.  Admin access still need to be allocated explicit.
 * @member {Boolean} no_permissions
 * @default false
 */
Study.prototype['no_permissions'] = false;

/**
 * @member {String} id
 */
Study.prototype['id'] = undefined;

/**
 * The identifiying name of the study. This can not be changed later. Must be a '[Slug](https://en.wikipedia.org/wiki/Clean_URL#Slug)'; A human and machine reable string containing no spaces, only numbers, lowered latin-script-letters and dashes. If you need to change the name later, use the display name.
 * @member {String} name
 */
Study.prototype['name'] = undefined;






export default Study;

